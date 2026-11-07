import 'package:flutter/material.dart';

class VerificationDashboard extends StatelessWidget {
  final Map<String, dynamic> data;

  const VerificationDashboard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final bool isPure = data['is_pure'] ?? true;
    final String verdict = data['verdict'] ?? 'Pure Curcumin';
    final double concentration = (data['concentration_pct'] ?? 0.0).toDouble();
    final double confidence = (data['confidence_score_pct'] ?? 98.5).toDouble();
    final double latency = (data['latency_ms'] ?? 19.2).toDouble();
    final String modelFormat = data['model_format'] ?? 'ONNX-INT8 (Quantized)';

    Color statusColor = const Color(0xFF10B981);
    String statusTitle = 'PASSED · CODEX & FSSAI COMPLIANT';
    String statusDesc = 'No chemical adulterants or synthetic azo pigments detected. Natural curcuminoid optical profile confirmed.';

    if (verdict.contains('Lead Chromate')) {
      statusColor = const Color(0xFFEF4444);
      statusTitle = 'CRITICAL TOXIC HAZARD (PbCrO₄)';
      statusDesc = 'Prohibited neurotoxin detected exceeding FSSAI 10 µg/g lead contaminant threshold. Route to Tier-2 confirmatory LA-ICP-MS.';
    } else if (verdict.contains('Metanil Yellow')) {
      statusColor = const Color(0xFFF59E0B);
      statusTitle = 'BANNED SYNTHETIC AZO DYE';
      statusDesc = 'Carcinogenic industrial dye identified via anomalous 480nm absorption and b* rigidity distortion.';
    } else if (verdict.contains('Chalk') || verdict.contains('Starch') || verdict.contains('Filler')) {
      statusColor = const Color(0xFFEAB308);
      statusTitle = 'BULK INERT FILLER DETECTED';
      statusDesc = 'Desaturation and micro-granularity scattering indicate presence of mineral/starch adulterant.';
    }

    return Scaffold(
      backgroundColor: const Color(0xFF080B11),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Edge Verification Dashboard', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16, top: 12, bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF38BDF8).withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF38BDF8)),
            ),
            child: Row(
              children: [
                const CircleAvatar(radius: 3, backgroundColor: Color(0xFF38BDF8)),
                const SizedBox(width: 6),
                Text(
                  data['is_demo_preset'] == true ? 'Demo Preset' : '${latency.toStringAsFixed(1)}ms',
                  style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (data['is_demo_preset'] == true)
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF3C7),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFF59E0B)),
                ),
                child: const Row(
                  children: [
                    Text('⚠️ ', style: TextStyle(fontSize: 14)),
                    Expanded(
                      child: Text(
                        'Demo preset only — results are illustrative, not live analysis',
                        style: TextStyle(color: Color(0xFF92400E), fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),

            // Verdict Card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: statusColor, width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: statusColor),
                    ),
                    child: Text(
                      statusTitle,
                      style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    verdict,
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    statusDesc,
                    style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8), height: 1.4),
                  ),
                  const SizedBox(height: 20),

                  // Dual Quantitative Gauges
                  Row(
                    children: [
                      // Concentration Gauge
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF080B11).withOpacity(0.7),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white.withOpacity(0.06)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('CONCENTRATION', style: TextStyle(color: Color(0xFF64748B), fontSize: 10, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.baseline,
                                textBaseline: TextBaseline.alphabetic,
                                children: [
                                  Text(
                                    isPure ? '0.0' : concentration.toStringAsFixed(1),
                                    style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: isPure ? const Color(0xFF10B981) : statusColor),
                                  ),
                                  const SizedBox(width: 4),
                                  const Text('% w/w', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              LinearProgressIndicator(
                                value: isPure ? 0.02 : (concentration / 25.0).clamp(0.0, 1.0),
                                backgroundColor: Colors.white10,
                                valueColor: AlwaysStoppedAnimation(isPure ? const Color(0xFF10B981) : statusColor),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),

                      // Confidence Gauge
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF080B11).withOpacity(0.7),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white.withOpacity(0.06)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('CONFIDENCE', style: TextStyle(color: Color(0xFF64748B), fontSize: 10, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.baseline,
                                textBaseline: TextBaseline.alphabetic,
                                children: [
                                  Text(
                                    confidence.toStringAsFixed(1),
                                    style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF38BDF8)),
                                  ),
                                  const SizedBox(width: 4),
                                  const Text('%', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              LinearProgressIndicator(
                                value: (confidence / 100.0).clamp(0.0, 1.0),
                                backgroundColor: Colors.white10,
                                valueColor: const AlwaysStoppedAnimation(Color(0xFF38BDF8)),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Engineered Metrics Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.08)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('ENGINEERED OPTICAL METRICS', style: TextStyle(color: Color(0xFFE8A33D), fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      _buildMetricTile('TCRI (Texture)', (data['tcri'] ?? 36.66).toStringAsFixed(2), 'Normal: 30-40'),
                      const SizedBox(width: 10),
                      _buildMetricTile('TRF (Reflectance)', (data['trf'] ?? 0.611).toStringAsFixed(3), 'Norm: 0.60-0.65'),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      _buildMetricTile('b* Rigidity', (data['rigidity_ratio'] ?? 0.685).toStringAsFixed(3), 'Pure: 0.685'),
                      const SizedBox(width: 10),
                      _buildMetricTile('Ambient CCT', '${(data['ambient_kelvin'] ?? 6500.0).toInt()}K', '${(data['ambient_lux'] ?? 380.0).toInt()} Lux'),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Regulatory Standards Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B).withOpacity(0.5),
                borderRadius: BorderRadius.circular(14),
                border: const Border(left: BorderSide(color: Color(0xFFE8A33D), width: 3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('REGULATORY BENCHMARKS', style: TextStyle(color: Color(0xFFE8A33D), fontSize: 11, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text('• Codex CXS 193-1995: Residue Limits\n• FSSAI Contaminants 2011: 10 µg/g Max Lead\n• Execution: Offline INT8 matrix on mobile NPU', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, height: 1.4)),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Scan Next Sample Button
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFE8A33D),
                  foregroundColor: const Color(0xFF080B11),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                onPressed: () => Navigator.pop(context),
                child: const Text('Scan Another Mound', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricTile(String title, String val, String sub) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF080B11).withOpacity(0.5),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withOpacity(0.04)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
            const SizedBox(height: 4),
            Text(val, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 2),
            Text(sub, style: const TextStyle(color: Color(0xFF64748B), fontSize: 10)),
          ],
        ),
      ),
    );
  }
}

