"""
Unit and integration tests for tools/dataset_ingest.py and train_on_real_dataset()
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.dataset_ingest import run_ingest
from core.models_ensemble import ensemble_model


def test_dataset_ingest_dry_run(tmp_path):
    samples_dir = 'static/samples'
    manifest_data = [
        {
            'sample_id': 'TEST-REAL-001',
            'filename': 'pure_alleppey.jpg',
            'source': 'Alleppey Farm A',
            'adulterant': 'pure',
            'concentration_pct': 0.0,
            'prep_date': '2026-11-08',
            'operator': 'Analyst 1'
        },
        {
            'sample_id': 'TEST-REAL-002',
            'filename': 'lead_chromate_8pct.jpg',
            'source': 'Mandi Wholesale B',
            'adulterant': 'lead_chromate',
            'concentration_pct': 8.0,
            'prep_date': '2026-11-08',
            'operator': 'Analyst 2'
        },
        {
            'sample_id': 'TEST-REAL-003',
            'filename': 'metanil_yellow_5pct.jpg',
            'source': 'Mandi Wholesale B',
            'adulterant': 'metanil_yellow',
            'concentration_pct': 5.0,
            'prep_date': '2026-11-08',
            'operator': 'Analyst 2'
        },
        {
            'sample_id': 'TEST-REAL-004',
            'filename': 'chalk_filler_15pct.jpg',
            'source': 'Retail Brand C',
            'adulterant': 'chalk',
            'concentration_pct': 15.0,
            'prep_date': '2026-11-08',
            'operator': 'Analyst 3'
        }
    ]

    manifest_file = tmp_path / "test_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    test_out_dir = tmp_path / "dataset_out"

    # 1. Test Dry Run
    dry_report = run_ingest(
        data_dir=samples_dir,
        manifest_path=str(manifest_file),
        output_dir=str(test_out_dir),
        dry_run=True,
        min_samples=150,
        min_sources=3
    )

    assert dry_report['status'] == 'SUCCESS'
    assert dry_report['is_dry_run'] is True
    assert dry_report['quality_passed_samples'] == 4
    assert dry_report['distinct_sources_count'] == 3
    assert len(dry_report['coverage_gaps']) > 0  # Should flag sample count gaps (<150)
    assert not test_out_dir.exists(), "Dry run must not create output directory"

    # 2. Test Active Ingest
    active_report = run_ingest(
        data_dir=samples_dir,
        manifest_path=str(manifest_file),
        output_dir=str(test_out_dir),
        dry_run=False,
        min_samples=150,
        min_sources=3
    )

    assert active_report['status'] == 'SUCCESS'
    assert active_report['is_dry_run'] is False
    assert test_out_dir.exists()
    assert (test_out_dir / "manifest.json").exists()
    assert (test_out_dir / "ingestion_report.json").exists()

    # 3. Test train_on_real_dataset
    metrics = ensemble_model.train_on_real_dataset(str(test_out_dir))
    assert metrics['data_source'] == "REAL"
    assert 'held_out_samples_evaluated' in metrics
    assert 'overall_classification_accuracy' in metrics
    assert ensemble_model.benchmark_metrics['data_source'] == "REAL"

