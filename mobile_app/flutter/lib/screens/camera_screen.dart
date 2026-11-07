import 'package:flutter/material.dart';
import 'verification_dashboard.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> with SingleTickerProviderStateMixin {
  bool _isAnalyzing = false;
  bool _isFrameValid = true;
  String _qualityPrompt = 'Frame Sharp · Illumination Balanced';
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  void _triggerInference([String? presetId]) async {
    setState(() => _isAnalyzing = true);

    // Emulate edge inference latency (<200ms)
    await Future.delayed(const Duration(milliseconds: 90));

    if (!mounted) return;
    setState(() => _isAnalyzing = false);

    // Sample payload
    final sampleResult = {
      'verdict': presetId == 'lead' ? 'Lead Chromate (PbCrO₄)' : 'Authentic Pure Turmeric',
      'is_pure': presetId != 'lead',
      'concentration_pct': presetId == 'lead' ? 8.4 : 0.0,
      'confidence_score_pct': 98.7,
      'latency_ms': 19.2,
      'tcri': 36.66,
      'trf': 0.611,
      'rigidity_ratio': 0.685,
      'ambient_lux': 380.0,
      'ambient_kelvin': 6500.0,
      'model_format': 'ONNX-INT8 (Edge NPU Native)',
      'class_probabilities': {
        'Pure': presetId == 'lead' ? 0.3 : 98.7,
        'Lead Chromate': presetId == 'lead' ? 98.4 : 0.4,
        'Metanil Yellow': 0.3,
        'Chalk Powder': 0.3,
        'Starch/Flour': 0.3,
      }
    };

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VerificationDashboard(data: sampleResult),
      ),
    );
  }

  void _showPresetPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F172A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select Lab Screening Preset',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 6),
            const Text(
              'Grounded in ISO/IEC 17025 multi-source sample evaluations',
              style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
            ),
            const SizedBox(height: 16),
            _buildPresetTile('Certified Pure Alleppey (GI-Tagged)', 'Pure · 0.0% Adulterant', () {
              Navigator.pop(ctx);
              _triggerInference('pure');
            }),
            _buildPresetTile('Lead Chromate (PbCrO₄) 8.0%', 'Industrial Toxic Pigment · 8.0% w/w', () {
              Navigator.pop(ctx);
              _triggerInference('lead');
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetTile(String title, String subtitle, VoidCallback onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: ListTile(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Text(subtitle, style: const TextStyle(color: Color(0xFFE8A33D), fontSize: 12)),
        trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: Color(0xFF38BDF8)),
        onTap: onTap,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final guideBoxSize = screenSize.width * 0.74;

    return Scaffold(
      body: Stack(
        children: [
          // Simulated Camera Preview
          Container(
            color: const Color(0xFF0D131F),
            child: Center(
              child: Container(
                width: 180,
                height: 180,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFFD97706).withOpacity(0.85),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.6),
                      blurRadius: 30,
                      spreadRadius: 10,
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Real-time Alignment Guide Box Overlay
          Center(
            child: SizedBox(
              width: guideBoxSize,
              height: guideBoxSize,
              child: CustomPaint(
                painter: AlignmentGuidePainter(
                  boxSize: guideBoxSize,
                  isValid: _isFrameValid,
                  pulseAnimation: _pulseController,
                ),
              ),
            ),
          ),

          // Top HUD Controls
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF101827).withOpacity(0.9),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFFE8A33D)),
                        ),
                        child: const Row(
                          children: [
                            CircleAvatar(radius: 4, backgroundColor: Color(0xFF10B981)),
                            SizedBox(width: 8),
                            Text(
                              'DYNAMIC ROI ACTIVE',
                              style: TextStyle(color: Color(0xFFE8A33D), fontSize: 11, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF101827).withOpacity(0.9),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.white12),
                        ),
                        child: const Text(
                          'CCT: 6500K D65',
                          style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Structural Quality Status Pill
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withOpacity(0.18),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF10B981)),
                    ),
                    child: Text(
                      '✓ $_qualityPrompt',
                      style: const TextStyle(color: Color(0xFF34D399), fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Bottom Shutter Controls
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  onPressed: _showPresetPicker,
                  icon: const Icon(Icons.science_outlined, color: Colors.white, size: 28),
                  tooltip: 'Lab Presets',
                ),
                GestureDetector(
                  onTap: _isAnalyzing ? null : () => _triggerInference(),
                  child: Container(
                    width: 78,
                    height: 78,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFFE8A33D), width: 4),
                      color: const Color(0xFFE8A33D).withOpacity(0.25),
                    ),
                    child: Center(
                      child: _isAnalyzing
                          ? const SizedBox(
                              width: 32,
                              height: 32,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3),
                            )
                          : Container(
                              width: 54,
                              height: 54,
                              decoration: const BoxDecoration(
                                shape: BoxShape.circle,
                                color: Color(0xFFE8A33D),
                              ),
                            ),
                    ),
                  ),
                ),
                const SizedBox(width: 48),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class AlignmentGuidePainter extends CustomPainter {
  final double boxSize;
  final bool isValid;
  final Animation<double> pulseAnimation;

  AlignmentGuidePainter({
    required this.boxSize,
    required this.isValid,
    required this.pulseAnimation,
  }) : super(repaint: pulseAnimation);

  @override
  void paint(Canvas canvas, Size size) {
    final borderColor = isValid ? const Color(0xFFE8A33D) : const Color(0xFFEF4444);

    final boxPaint = Paint()
      ..color = borderColor.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(0, 0, boxSize, boxSize),
      const Radius.circular(16),
    );
    canvas.drawRRect(rect, boxPaint);

    // 4 Corner Brackets
    final cornerPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round;

    const arm = 24.0;
    // Top-Left
    canvas.drawLine(const Offset(0, 0), const Offset(arm, 0), cornerPaint);
    canvas.drawLine(const Offset(0, 0), const Offset(0, arm), cornerPaint);
    // Top-Right
    canvas.drawLine(Offset(boxSize, 0), Offset(boxSize - arm, 0), cornerPaint);
    canvas.drawLine(Offset(boxSize, 0), Offset(boxSize, arm), cornerPaint);
    // Bottom-Left
    canvas.drawLine(Offset(0, boxSize), Offset(arm, boxSize), cornerPaint);
    canvas.drawLine(Offset(0, boxSize), Offset(0, boxSize - arm), cornerPaint);
    // Bottom-Right
    canvas.drawLine(Offset(boxSize, boxSize), Offset(boxSize - arm, boxSize), cornerPaint);
    canvas.drawLine(Offset(boxSize, boxSize), Offset(boxSize, boxSize - arm), cornerPaint);

    // Center Crosshair
    final centerPaint = Paint()
      ..color = borderColor.withOpacity(0.6)
      ..strokeWidth = 1.0;

    final center = boxSize / 2;
    canvas.drawLine(Offset(center - 14, center), Offset(center + 14, center), centerPaint);
    canvas.drawLine(Offset(center, center - 14), Offset(center, center + 14), centerPaint);

    // Petri dish circular dashed guide
    final circlePaint = Paint()
      ..color = Colors.white.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawCircle(Offset(center, center), boxSize * 0.38, circlePaint);
  }

  @override
  bool shouldRepaint(covariant AlignmentGuidePainter oldDelegate) => true;
}

