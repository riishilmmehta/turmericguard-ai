"""
TurmericGuard AI — Fleet Management & Optical Drift Monitoring
Implements Section 5.3, 6.5, and 7.4 of the Technical Specification:
- Device registry covering Lab-Grade units (RPi 4/5) and Field units (ESP32)
- Reference tile optical calibration event logging
- Sensor aging and ambient light leakage drift monitoring
- Fleet status and scheduled maintenance alerts
"""

import time
import hashlib
from datetime import datetime


class FleetManager:
    """Manages connected sensor units, calibration routines, and drift alerts."""

    def __init__(self):
        self.devices = {
            "TG-RPi5-LAB-01": {
                "device_id": "TG-RPi5-LAB-01",
                "sku": "Lab-Grade Unit (RPi 5 + Vis-SWNIR)",
                "location": "Central Food Safety Laboratory, New Delhi",
                "firmware_version": "v2.4.1-prod",
                "sensor_type": "Vis-SWNIR Hyperspectral (400-1000nm)",
                "enclosure_seal": "Hermetic Acrylic Lab Enclosure",
                "calibration_state": {
                    "last_calibrated": "2026-11-01T08:30:00Z",
                    "white_tile_reflectance_pct": 99.4,
                    "dark_current_mv": 1.2,
                    "calibration_hash": "a4f89d31c4b12e88b4d081912a",
                    "tests_since_last_cal": 18
                },
                "drift_metrics": {
                    "drift_pct": 0.6,
                    "drift_status": "OPTIMAL",
                    "led_ring_temp_c": 31.5,
                    "ambient_light_leakage_lux": 0.02
                },
                "total_tests_conducted": 1420,
                "is_online": True
            },
            "TG-ESP32-FLD-01": {
                "device_id": "TG-ESP32-FLD-01",
                "sku": "Field Unit (ESP32 + AS7265x NIR)",
                "location": "APMC Mandi Checkpoint Yard, Nizamabad, Telangana",
                "firmware_version": "v1.9.0-tinyml",
                "sensor_type": "AS7265x 18-Channel Tri-Spectral",
                "enclosure_seal": "3D-Printed Field Light-Shine Enclosure",
                "calibration_state": {
                    "last_calibrated": "2026-10-31T14:15:00Z",
                    "white_tile_reflectance_pct": 97.8,
                    "dark_current_mv": 3.8,
                    "calibration_hash": "c8e219ba48f7129188d0112c33",
                    "tests_since_last_cal": 42
                },
                "drift_metrics": {
                    "drift_pct": 2.2,
                    "drift_status": "NORMAL",
                    "led_ring_temp_c": 36.2,
                    "ambient_light_leakage_lux": 0.08
                },
                "total_tests_conducted": 875,
                "is_online": True
            },
            "TG-ESP32-FLD-02": {
                "device_id": "TG-ESP32-FLD-02",
                "sku": "Field Unit (ESP32 + AS7265x NIR)",
                "location": "Spices Board Regulated Market, Erode, Tamil Nadu",
                "firmware_version": "v1.9.0-tinyml",
                "sensor_type": "AS7265x 18-Channel Tri-Spectral",
                "enclosure_seal": "3D-Printed Field Light-Shine Enclosure",
                "calibration_state": {
                    "last_calibrated": "2026-10-28T09:00:00Z",
                    "white_tile_reflectance_pct": 95.1,
                    "dark_current_mv": 6.1,
                    "calibration_hash": "77bc1094df821735160aa114ef",
                    "tests_since_last_cal": 68
                },
                "drift_metrics": {
                    "drift_pct": 4.9,
                    "drift_status": "DRIFT_ALERT",
                    "led_ring_temp_c": 39.4,
                    "ambient_light_leakage_lux": 0.22
                },
                "total_tests_conducted": 1130,
                "is_online": True
            },
            "TG-RPi5-LAB-02": {
                "device_id": "TG-RPi5-LAB-02",
                "sku": "Lab-Grade Unit (RPi 5 + Vis-SWNIR)",
                "location": "Spice Quality Assessment Centre, Cochin, Kerala",
                "firmware_version": "v2.4.1-prod",
                "sensor_type": "Vis-SWNIR Hyperspectral (400-1000nm)",
                "enclosure_seal": "Hermetic Acrylic Lab Enclosure",
                "calibration_state": {
                    "last_calibrated": "2026-11-02T06:00:00Z",
                    "white_tile_reflectance_pct": 99.8,
                    "dark_current_mv": 0.9,
                    "calibration_hash": "55de31ac9912beff4031920acb",
                    "tests_since_last_cal": 5
                },
                "drift_metrics": {
                    "drift_pct": 0.2,
                    "drift_status": "OPTIMAL",
                    "led_ring_temp_c": 29.8,
                    "ambient_light_leakage_lux": 0.01
                },
                "total_tests_conducted": 640,
                "is_online": True
            }
        }

    def list_devices(self):
        """Returns fleet inventory with health and calibration summaries."""
        return list(self.devices.values())

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def log_calibration_event(self, device_id, white_tile_reflectance=99.2, dark_current_mv=1.5):
        """Logs a field calibration routine against the certified reference tile."""
        device = self.devices.get(device_id)
        if not device:
            # Auto-register new field unit
            device = {
                "device_id": device_id,
                "sku": "Field Unit (ESP32 / RPi)",
                "location": "Mandi Station",
                "firmware_version": "v2.0.0",
                "sensor_type": "NIR/Hyperspectral",
                "enclosure_seal": "Standard Enclosure",
                "calibration_state": {},
                "drift_metrics": {},
                "total_tests_conducted": 0,
                "is_online": True
            }
            self.devices[device_id] = device

        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        cal_payload = f"{device_id}:{now_iso}:{white_tile_reflectance}:{dark_current_mv}"
        cal_hash = hashlib.sha256(cal_payload.encode('utf-8')).hexdigest()[:26]

        drift_pct = max(0.1, round(abs(100.0 - white_tile_reflectance), 2))
        status = "OPTIMAL" if drift_pct < 1.5 else ("NORMAL" if drift_pct < 3.5 else "DRIFT_ALERT")

        device["calibration_state"] = {
            "last_calibrated": now_iso,
            "white_tile_reflectance_pct": round(float(white_tile_reflectance), 2),
            "dark_current_mv": round(float(dark_current_mv), 2),
            "calibration_hash": cal_hash,
            "tests_since_last_cal": 0
        }

        device["drift_metrics"] = {
            "drift_pct": drift_pct,
            "drift_status": status,
            "led_ring_temp_c": 32.0,
            "ambient_light_leakage_lux": 0.02
        }

        return {
            "success": True,
            "device_id": device_id,
            "calibration_timestamp": now_iso,
            "calibration_hash": cal_hash,
            "drift_percentage": drift_pct,
            "drift_status": status,
            "message": "Field calibration routine completed successfully. White-balance baseline refreshed."
        }

    def get_device_drift_status(self, device_id):
        """Returns drift-monitoring status per Section 7.2."""
        device = self.devices.get(device_id)
        if not device:
            return {"error": f"Device {device_id} not found", "drift_status": "UNKNOWN"}

        drift = device["drift_metrics"]
        cal = device["calibration_state"]

        action_required = drift["drift_pct"] >= 3.5
        recalibration_due = cal["tests_since_last_cal"] >= 50

        return {
            "device_id": device_id,
            "sku": device["sku"],
            "location": device["location"],
            "drift_pct": drift["drift_pct"],
            "drift_status": drift["drift_status"],
            "action_required": action_required,
            "recalibration_due": recalibration_due,
            "tests_since_calibration": cal["tests_since_last_cal"],
            "calibration_state": cal,
            "recommendation": (
                "Device optical sensor within calibrated tolerance."
                if not action_required else
                "Optical drift exceeds 3.5% threshold! Run white-tile recalibration before conducting official regulatory tests."
            )
        }


fleet_manager = FleetManager()
