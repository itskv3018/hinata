// utils/constants.dart
// App-wide constants.

class AppConstants {
  static const String appName = 'Hinata';
  static const String appVersion = '0.1.0';
  static const String agentEmoji = '🌸';

  // Default server URL (change to your server's IP)
  static const String defaultServerUrl = 'http://localhost:8000';
  static const String defaultWsUrl = 'ws://localhost:8000/ws';

  // Voice
  static const String wakeWord = 'hey hinata';

  // Animation durations
  static const Duration shortAnim = Duration(milliseconds: 200);
  static const Duration mediumAnim = Duration(milliseconds: 400);
  static const Duration longAnim = Duration(milliseconds: 800);
}
