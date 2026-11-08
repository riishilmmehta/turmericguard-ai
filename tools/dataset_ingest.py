#!/usr/bin/env python3
"""
TurmericGuard AI — Real Dataset Ingestion Pipeline & Quality Gate CLI
Accepts a raw folder of sample photos + a CSV or JSON manifest with lab metadata:
  source (farm/market/brand), adulterant, concentration_pct, prep_date, operator.

Executes:
1. Manifest validation (schema, concentration bounds 0.0-100.0%, file existence, uniqueness).
2. Vision quality check (Laplacian blur variance and specular glare index via core.vision_pipeline).
3. Standardized dataset organization:
     dataset/real/v1/{adulterant}/{concentration_band}/...
4. Comprehensive gap analysis and summary statistics against international minimum standards
   (>=150-200 samples per band across >=3 distinct sources).
5. Supports --dry-run for validation without writes.
"""

import os
import sys
import json
import csv
import shutil
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Add project root to sys.path for core imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PIL import Image
from core.vision_pipeline import check_image_quality

# Canonical schema constants
VALID_ADULTERANTS = {
    'none': 'pure',
    'pure': 'pure',
    'lead_chromate': 'lead_chromate',
    'metanil_yellow': 'metanil_yellow',
    'chalk': 'chalk',
    'chalk_filler': 'chalk',
    'starch_chalk_filler': 'chalk',
    'cassava': 'cassava',
    'cassava_starch': 'cassava',
    'acid_orange_7': 'acid_orange_7'
}

CONCENTRATION_BANDS = ['pure', 'trace', 'moderate', 'heavy']

RECOMMENDED_MIN_SAMPLES_PER_BAND = 150
RECOMMENDED_MIN_SOURCES = 3


def get_concentration_band(adulterant: str, concentration_pct: float) -> str:
    """Categorizes concentration into standard epidemiological & analytical bands."""
    if adulterant == 'pure' or concentration_pct <= 0.001:
        return 'pure'
    elif concentration_pct < 5.0:
        return 'trace'
    elif concentration_pct <= 15.0:
        return 'moderate'
    else:
        return 'heavy'


def parse_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Loads manifest from CSV or JSON file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    records = []
    if manifest_path.endswith('.json'):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'samples' in data:
                records = data['samples']
            else:
                raise ValueError("JSON manifest must be a list of records or contain a 'samples' array.")
    elif manifest_path.endswith('.csv'):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    else:
        raise ValueError(f"Unsupported manifest format: {manifest_path}. Must be .csv or .json")

    return records


def validate_manifest_record(record: Dict[str, Any], data_dir: str, seen_ids: set) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validates an individual sample metadata record."""
    sample_id = str(record.get('sample_id', '')).strip()
    if not sample_id:
        return False, "Missing required 'sample_id'", record

    if sample_id in seen_ids:
        return False, f"Duplicate sample_id detected: {sample_id}", record
    seen_ids.add(sample_id)

    # Photo filename
    filename = record.get('filename') or record.get('photo_path') or record.get('image')
    if not filename:
        return False, f"Sample {sample_id}: Missing image filename", record

    file_path = os.path.join(data_dir, filename)
    if not os.path.exists(file_path):
        return False, f"Sample {sample_id}: Referenced image file not found: {file_path}", record

    # Source
    source = str(record.get('source', '')).strip()
    if not source:
        return False, f"Sample {sample_id}: Missing 'source' (e.g. farm/market/brand/regional origin)", record

    # Adulterant
    raw_adulterant = str(record.get('adulterant', '')).strip().lower().replace(' ', '_').replace('-', '_')
    if raw_adulterant not in VALID_ADULTERANTS:
        return False, f"Sample {sample_id}: Invalid adulterant '{raw_adulterant}'. Must be one of {list(VALID_ADULTERANTS.keys())}", record
    canonical_adulterant = VALID_ADULTERANTS[raw_adulterant]

    # Concentration
    try:
        conc_pct = float(record.get('concentration_pct', 0.0))
    except (ValueError, TypeError):
        return False, f"Sample {sample_id}: Invalid concentration_pct '{record.get('concentration_pct')}'. Must be numeric.", record

    if conc_pct < 0.0 or conc_pct > 100.0:
        return False, f"Sample {sample_id}: concentration_pct ({conc_pct}) out of physical bounds [0.0, 100.0]", record

    if canonical_adulterant == 'pure' and conc_pct > 0.001:
        return False, f"Sample {sample_id}: Pure turmeric sample cannot have non-zero concentration ({conc_pct}%)", record

    prep_date = str(record.get('prep_date', '')).strip() or datetime.utcnow().strftime('%Y-%m-%d')
    operator = str(record.get('operator', '')).strip() or 'Unknown Operator'

    cleaned = {
        'sample_id': sample_id,
        'filename': filename,
        'file_path': file_path,
        'source': source,
        'adulterant': canonical_adulterant,
        'concentration_pct': round(conc_pct, 2),
        'concentration_band': get_concentration_band(canonical_adulterant, conc_pct),
        'prep_date': prep_date,
        'operator': operator
    }
    return True, None, cleaned


def run_ingest(
    data_dir: str,
    manifest_path: str,
    output_dir: str = 'dataset/real/v1',
    dry_run: bool = False,
    min_samples: int = RECOMMENDED_MIN_SAMPLES_PER_BAND,
    min_sources: int = RECOMMENDED_MIN_SOURCES
) -> Dict[str, Any]:
    """Executes the ingestion, validation, quality check, gap analysis, and file organization."""
    print("=" * 70)
    print("🌿 TURMERICGUARD AI — REAL DATASET INGESTION & QUALITY PIPELINE")
    print("=" * 70)
    print(f"Data Directory:     {os.path.abspath(data_dir)}")
    print(f"Manifest File:      {os.path.abspath(manifest_path)}")
    print(f"Target Directory:   {os.path.abspath(output_dir)}")
    print(f"Execution Mode:     {'DRY-RUN (Validation only, no writes)' if dry_run else 'ACTIVE INGESTION'}")
    print("-" * 70)

    raw_records = parse_manifest(manifest_path)
    print(f"Loaded {len(raw_records)} records from manifest.")

    seen_ids = set()
    validated_records = []
    manifest_errors = []

    # 1. Validate manifest records
    for raw in raw_records:
        ok, err_msg, cleaned = validate_manifest_record(raw, data_dir, seen_ids)
        if ok:
            validated_records.append(cleaned)
        else:
            manifest_errors.append(err_msg)

    if manifest_errors:
        print(f"\n⚠️  {len(manifest_errors)} MANIFEST VALIDATION ERROR(S):")
        for err in manifest_errors[:10]:
            print(f"   • {err}")
        if len(manifest_errors) > 10:
            print(f"   • ... and {len(manifest_errors) - 10} more.")

    # 2. Vision Quality Screening
    accepted_samples = []
    rejected_quality_samples = []

    print("\n🔍 Executing Optical Quality Checks (Laplacian Blur & Glare Analysis)...")
    for rec in validated_records:
        file_path = rec['file_path']
        try:
            pil_img = Image.open(file_path).convert('RGB')
            q_res = check_image_quality(pil_img)
            rec['quality_metrics'] = q_res

            if q_res['is_valid']:
                accepted_samples.append(rec)
            else:
                rec['rejection_reason'] = q_res['rejection_prompt']
                rec['rejection_code'] = q_res['rejection_code']
                rejected_quality_samples.append(rec)
        except Exception as e:
            rec['rejection_reason'] = f"Corrupted image file: {str(e)}"
            rec['rejection_code'] = "FILE_CORRUPT"
            rejected_quality_samples.append(rec)

    print(f"Quality screening complete:")
    print(f"   ✓ Passed quality check:   {len(accepted_samples)} samples")
    print(f"   ✗ Rejected by quality:    {len(rejected_quality_samples)} samples")

    if rejected_quality_samples:
        print("\nQuality rejection details:")
        for r in rejected_quality_samples[:5]:
            print(f"   • {r['sample_id']} ({r['filename']}): [{r.get('rejection_code')}] {r.get('rejection_reason')}")
        if len(rejected_quality_samples) > 5:
            print(f"   • ... and {len(rejected_quality_samples) - 5} more.")

    # 3. Compute Summary Statistics & Coverage Gap Analysis
    total_accepted = len(accepted_samples)
    adulterant_counts: Dict[str, int] = {}
    band_counts: Dict[str, Dict[str, int]] = {}
    sources_per_adulterant: Dict[str, set] = {}
    all_sources = set()

    for rec in accepted_samples:
        ad = rec['adulterant']
        band = rec['concentration_band']
        src = rec['source']

        adulterant_counts[ad] = adulterant_counts.get(ad, 0) + 1
        all_sources.add(src)

        if ad not in band_counts:
            band_counts[ad] = {'pure': 0, 'trace': 0, 'moderate': 0, 'heavy': 0}
        band_counts[ad][band] += 1

        if ad not in sources_per_adulterant:
            sources_per_adulterant[ad] = set()
        sources_per_adulterant[ad].add(src)

    # Gap Analysis Warnings
    gap_warnings = []
    for ad, bands in band_counts.items():
        distinct_srcs = len(sources_per_adulterant.get(ad, set()))
        if distinct_srcs < min_sources:
            gap_warnings.append(
                f"WARNING: '{ad}' has only {distinct_srcs} distinct sources ({', '.join(sources_per_adulterant.get(ad, [])) or 'none'}), "
                f"minimum recommended is >={min_sources} across different farms/markets/brands."
            )

        if ad == 'pure':
            pure_cnt = bands.get('pure', 0)
            if pure_cnt < min_samples:
                gap_warnings.append(
                    f"WARNING: Authentic Pure Turmeric has only {pure_cnt} samples, minimum recommended is >={min_samples}."
                )
        else:
            for b_name in ['trace', 'moderate', 'heavy']:
                cnt = bands.get(b_name, 0)
                if cnt < min_samples:
                    gap_warnings.append(
                        f"WARNING: {ad.replace('_', ' ').title()} ({b_name} band) has only {cnt} samples, "
                        f"minimum recommended is >={min_samples} across >={min_sources} distinct sources."
                    )

    # 4. Organize files and write canonical manifest (if not dry run)
    ingested_paths = []
    if not dry_run and accepted_samples:
        os.makedirs(output_dir, exist_ok=True)

        for rec in accepted_samples:
            target_subdir = os.path.join(output_dir, rec['adulterant'], rec['concentration_band'])
            os.makedirs(target_subdir, exist_ok=True)

            ext = os.path.splitext(rec['filename'])[1] or '.jpg'
            dest_filename = f"{rec['sample_id']}_{os.path.basename(rec['filename'])}"
            dest_path = os.path.join(target_subdir, dest_filename)

            shutil.copy2(rec['file_path'], dest_path)
            rec['standardized_path'] = os.path.relpath(dest_path, output_dir).replace('\\', '/')
            ingested_paths.append(dest_path)

        # Write canonical manifest.json
        canonical_manifest = {
            'dataset_version': '1.0.0-real',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'total_samples': total_accepted,
            'sources': sorted(list(all_sources)),
            'adulterant_classes': sorted(list(adulterant_counts.keys())),
            'samples': accepted_samples
        }
        manifest_dest = os.path.join(output_dir, 'manifest.json')
        with open(manifest_dest, 'w', encoding='utf-8') as f:
            json.dump(canonical_manifest, f, indent=2)

    # Compile Final Report
    report = {
        'status': 'SUCCESS' if not manifest_errors else 'PARTIAL_COMPLETION',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'is_dry_run': dry_run,
        'manifest_records_read': len(raw_records),
        'manifest_errors_count': len(manifest_errors),
        'quality_passed_samples': total_accepted,
        'quality_rejected_samples': len(rejected_quality_samples),
        'distinct_sources_count': len(all_sources),
        'distinct_sources': sorted(list(all_sources)),
        'distribution_by_adulterant': adulterant_counts,
        'distribution_by_concentration_band': band_counts,
        'coverage_gaps': gap_warnings,
        'output_directory': output_dir if not dry_run else None
    }

    if not dry_run and output_dir:
        report_dest = os.path.join(output_dir, 'ingestion_report.json')
        with open(report_dest, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    # Print Summary Table
    print("\n" + "=" * 70)
    print("📊 INGESTION SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total Usable Samples Ingested: {total_accepted}")
    print(f"Distinct Geographic/Brand Sources: {len(all_sources)} ({', '.join(sorted(all_sources)) or 'None'})")
    print("\nClass & Band Breakdown:")
    for ad, bands in band_counts.items():
        total_ad = adulterant_counts.get(ad, 0)
        print(f"  • {ad.ljust(20)}: {str(total_ad).rjust(4)} total | Pure: {bands.get('pure',0)} | Trace (<5%): {bands.get('trace',0)} | Mod (5-15%): {bands.get('moderate',0)} | Heavy (>15%): {bands.get('heavy',0)}")

    print("\n🚨 COVERAGE GAP ANALYSIS:")
    if gap_warnings:
        for gw in gap_warnings:
            print(f"  ⚠️  {gw}")
    else:
        print("  ✓ Full physical coverage achieved: All classes meet recommended targets (>=150 samples/band, >=3 sources).")

    print("=" * 70)
    return report


def main():
    parser = argparse.ArgumentParser(description="TurmericGuard AI Real Dataset Ingestion & Validation Pipeline")
    parser.add_argument('--data-dir', required=True, help="Path to directory containing sample photos")
    parser.add_argument('--manifest', required=True, help="Path to CSV or JSON manifest file")
    parser.add_argument('--output-dir', default='dataset/real/v1', help="Target directory for standardized dataset")
    parser.add_argument('--dry-run', action='store_true', help="Validate manifest & image quality without copying files")
    parser.add_argument('--min-samples', type=int, default=RECOMMENDED_MIN_SAMPLES_PER_BAND, help="Minimum sample count per band")
    parser.add_argument('--min-sources', type=int, default=RECOMMENDED_MIN_SOURCES, help="Minimum distinct sources per class")

    args = parser.parse_args()
    report = run_ingest(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        min_samples=args.min_samples,
        min_sources=args.min_sources
    )

    if report['manifest_errors_count'] > 0 and report['quality_passed_samples'] == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

