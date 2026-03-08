// services/settings_service.dart
// Persistent settings using SharedPreferences.

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/constants.dart';

class SettingsService extends ChangeNotifier {
  late SharedPreferences _prefs;

  // Settings with defaults
  String _serverUrl = AppConstants.defaultServerUrl;
  bool _voiceEnabled = true;
  bool _autoSpeak = true;       // Auto-speak bot responses
  bool _darkMode = true;
  String _userName = '';
  bool _hapticFeedback = true;

  // Getters
  String get serverUrl => _serverUrl;
  bool get voiceEnabled => _voiceEnabled;
  bool get autoSpeak => _autoSpeak;
  bool get darkMode => _darkMode;
  String get userName => _userName;
  bool get hapticFeedback => _hapticFeedback;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _serverUrl = _prefs.getString('server_url') ?? AppConstants.defaultServerUrl;
    _voiceEnabled = _prefs.getBool('voice_enabled') ?? true;
    _autoSpeak = _prefs.getBool('auto_speak') ?? true;
    _darkMode = _prefs.getBool('dark_mode') ?? true;
    _userName = _prefs.getString('user_name') ?? '';
    _hapticFeedback = _prefs.getBool('haptic_feedback') ?? true;
    notifyListeners();
  }

  // Setters
  Future<void> setServerUrl(String url) async {
    _serverUrl = url;
    await _prefs.setString('server_url', url);
    notifyListeners();
  }

  Future<void> setVoiceEnabled(bool enabled) async {
    _voiceEnabled = enabled;
    await _prefs.setBool('voice_enabled', enabled);
    notifyListeners();
  }

  Future<void> setAutoSpeak(bool enabled) async {
    _autoSpeak = enabled;
    await _prefs.setBool('auto_speak', enabled);
    notifyListeners();
  }

  Future<void> setDarkMode(bool enabled) async {
    _darkMode = enabled;
    await _prefs.setBool('dark_mode', enabled);
    notifyListeners();
  }

  Future<void> setUserName(String name) async {
    _userName = name;
    await _prefs.setString('user_name', name);
    notifyListeners();
  }

  Future<void> setHapticFeedback(bool enabled) async {
    _hapticFeedback = enabled;
    await _prefs.setBool('haptic_feedback', enabled);
    notifyListeners();
  }
}
