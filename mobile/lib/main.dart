// main.dart
// Entry point for the Hinata mobile app.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import 'services/chat_service.dart';
import 'services/voice_service.dart';
import 'services/settings_service.dart';
import 'screens/home_screen.dart';
import 'screens/splash_screen.dart';
import 'utils/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock orientation to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0D0D1A),
    ),
  );

  final settings = SettingsService();
  await settings.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ChatService()),
        ChangeNotifierProvider(create: (_) => VoiceService()),
        ChangeNotifierProvider.value(value: settings),
      ],
      child: const HinataApp(),
    ),
  );
}

class HinataApp extends StatelessWidget {
  const HinataApp({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsService>();

    return MaterialApp(
      title: 'Hinata',
      debugShowCheckedModeBanner: false,
      theme: HinataTheme.darkTheme,
      darkTheme: HinataTheme.darkTheme,
      themeMode: ThemeMode.dark,
      home: const SplashScreen(),
    );
  }
}
