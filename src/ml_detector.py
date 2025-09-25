"""
ml_detector.py — детектор аномалий трафика
"""

import os
import time
import logging
import random
from datetime import datetime
from typing import Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv

import db  # get_conn, list_tracked_domains, insert_metric_sample, get_current_state, set_state

# ---------- конфигурация ----------
load_dotenv()

# === Логирование в консоль ===
import logging, os, sys

def _setup_ml_console_logger():
    lvl = os.getenv("ML_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, lvl, logging.INFO)

    lg = logging.getLogger("ml_detector")
    lg.setLevel(level)
    lg.propagate = False

    has_stream = any(isinstance(h, logging.StreamHandler) for h in lg.handlers)
    if not has_stream:
        sh = logging.StreamHandler(stream=sys.stdout) 
        sh.setLevel(level)
        sh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s - %(message)s"
        ))
        lg.addHandler(sh)

    logging.getLogger("ddos_app.db").propagate = False

    return lg

logger = _setup_ml_console_logger()

INTERVAL_SEC = int(os.getenv("ML_INTERVAL", "10"))
BASELINE_SAMPLES = int(os.getenv("BASELINE_SAMPLES", "600"))
P_ATTACK = float(os.getenv("P_ATTACK", "0.12"))
IFOREST_THRESHOLD = float(os.getenv("IFOREST_THRESHOLD", "-0.05"))

BASE_NORMAL = dict(
    packets_mean=1200, packets_std=250,
    uniq_ips_mean=45, uniq_ips_std=12,
    bytes_mean=1.2e6, bytes_std=2.2e5
)
ATTACK = dict(
    packets_mean=55000, packets_std=6000,
    uniq_ips_mean=600,  uniq_ips_std=150,
    bytes_mean=6.0e7,   bytes_std=8.0e6
)

def now_trunc_sec() -> datetime:
    return datetime.now().replace(microsecond=0)

def sample_metrics() -> np.ndarray:
    if random.random() < P_ATTACK:
        pm, ps = ATTACK["packets_mean"], ATTACK["packets_std"]
        im, istd = ATTACK["uniq_ips_mean"], ATTACK["uniq_ips_std"]
        bm, bs = ATTACK["bytes_mean"], ATTACK["bytes_std"]
    else:
        pm, ps = BASE_NORMAL["packets_mean"], BASE_NORMAL["packets_std"]
        im, istd = BASE_NORMAL["uniq_ips_mean"], BASE_NORMAL["uniq_ips_std"]
        bm, bs = BASE_NORMAL["bytes_mean"], BASE_NORMAL["bytes_std"]
    pps = max(0, random.gauss(pm, ps))
    uniq = max(0, random.gauss(im, istd))
    bps = max(0, random.gauss(bm, bs))
    return np.array([pps, uniq, bps], dtype=float)

def sample_src_ips(uniq_count: int, cap: int = 50) -> list[str]:
    
    #Генерация активных IP за тик

    n = max(0, min(int(uniq_count), cap))
    ips = []
    for _ in range(n):
        # простая генерация IPv4
        a, b, c, d = (random.randint(1, 254) for _ in range(4))
        ips.append(f"{a}.{b}.{c}.{d}")
    return ips

class DomainIForest:
    def __init__(self, contamination=0.03, seed=42):
        self.model = IsolationForest(contamination=contamination, random_state=seed)
        self.threshold = IFOREST_THRESHOLD
        self.fitted = False

    def fit_baseline(self, n=BASELINE_SAMPLES):
        X = []
        for _ in range(n):
            pm, ps = BASE_NORMAL["packets_mean"], BASE_NORMAL["packets_std"]
            im, istd = BASE_NORMAL["uniq_ips_mean"], BASE_NORMAL["uniq_ips_std"]
            bm, bs = BASE_NORMAL["bytes_mean"], BASE_NORMAL["bytes_std"]
            pps = max(0, random.gauss(pm, ps))
            uniq = max(0, random.gauss(im, istd))
            bps = max(0, random.gauss(bm, bs))
            X.append([pps, uniq, bps])
        self.model.fit(np.array(X, dtype=float))
        self.fitted = True

    def score(self, vec: np.ndarray) -> float:
        if not self.fitted:
            self.fit_baseline()
        return float(self.model.decision_function([vec])[0])

    def is_attack(self, score: float) -> bool:
        return score < self.threshold

def process_domain_tick(domain_row: Dict, det: DomainIForest):
    domain_id = domain_row["id"]
    domain = domain_row["domain"]
    ts_now = now_trunc_sec()

    vec = sample_metrics()
    score = det.score(vec)
    is_ddos = det.is_attack(score)
    target_state = "ddos" if is_ddos else "active"

    pps = int(vec[0])
    uniq = int(vec[1])
    bps = int(vec[2])

    # генерируем список IPv4 (до 20 адресов)
    src_ips = sample_src_ips(uniq, cap=20)

    db.insert_metric_sample(
        domain_id=domain_id,
        ts=ts_now,
        pps=pps,
        uniq_ips=uniq,
        bytes_per_s=int(bps),
        ok=not is_ddos,
        source="ml_detector",
        extra={"score": score},
        src_ips=src_ips,
    )


    st = db.get_current_state(domain_id)
    current = st["state"] if st else None

    if current != target_state:
        db.set_state(
            domain_id=domain_id,
            new_state=target_state,
            ts=ts_now,
            details={"model": "IsolationForest", "score": score}
        )
        logger.info(
            "STATE CHANGE domain=%s: %s -> %s (score=%.4f, pps=%d uniq=%d bps=%d)",
            domain, current, target_state, score, pps, uniq, bps
        )
    else:
        logger.debug("NO CHANGE domain=%s state=%s score=%.4f", domain, current, score)

def main():
    detectors: Dict[int, DomainIForest] = {}  # domain_id -> model

    try:
        while True:
            cycle_start = time.time()

            # каждый тик берём актуальный список доменов
            try:
                current_domains: List[Dict] = db.list_tracked_domains()
            except Exception as e:
                logger.error("Не удалось получить список доменов: %s", e)
                current_domains = []

            # синхронизируем пул детекторов с БД
            current_ids = {d["id"] for d in current_domains}
            # добавим новые
            for d in current_domains:
                if d["id"] not in detectors:
                    detectors[d["id"]] = DomainIForest()
                    logger.info("Detector initialized for NEW domain=%s (id=%s)", d["domain"], d["id"])
            # уберём удалённые
            for stale_id in list(detectors.keys()):
                if stale_id not in current_ids:
                    logger.info("Removing detector for deleted domain_id=%s", stale_id)
                    detectors.pop(stale_id, None)

            if not current_domains:
                time.sleep(INTERVAL_SEC)
                continue

            # обработка всех актуальных доменов
            for d in current_domains:
                try:
                    det = detectors.get(d["id"])
                    if det is None:

                        det = DomainIForest()
                        detectors[d["id"]] = det
                    process_domain_tick(d, det)
                except Exception as e:
                    logger.error("Domain loop error for %s: %s", d.get("domain"), e)

            # интервал
            elapsed = time.time() - cycle_start
            sleep_left = max(0.0, INTERVAL_SEC - elapsed)
            time.sleep(sleep_left)

    except KeyboardInterrupt:
        logger.info("Detector stopped by user")

if __name__ == "__main__":
    main()
