import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/camera_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: Color(0xFF080B11),
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  runApp(const TurmericGuardApp());
}

class TurmericGuardApp extends StatelessWidget {
  const TurmericGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TurmericGuard AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF080B11),
        primaryColor: const Color(0xFFE8A33D),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFE8A33D),
          secondary: Color(0xFF38BDF8),
          surface: Color(0xFF0F172A),
          error: Color(0xFFEF4444),
        ),
        fontFamily: 'Roboto',
      ),
      home: const CameraScreen(),
    );
  }
}

