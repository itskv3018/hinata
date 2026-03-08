// services/voice_service.dart
// Speech-to-text and text-to-speech for mobile.

import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';

class VoiceService extends ChangeNotifier {
  final stt.SpeechToText _speechToText = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();

  bool _isListening = false;
  bool _isSpeaking = false;
  bool _speechAvailable = false;
  String _lastWords = '';
  double _confidence = 0.0;

  // Getters
  bool get isListening => _isListening;
  bool get isSpeaking => _isSpeaking;
  bool get speechAvailable => _speechAvailable;
  String get lastWords => _lastWords;
  double get confidence => _confidence;

  // ---------------------------------------------------------------
  // Initialization
  // ---------------------------------------------------------------

  Future<void> init() async {
    // Init STT
    _speechAvailable = await _speechToText.initialize(
      onError: (error) => print('STT Error: $error'),
      onStatus: (status) => print('STT Status: $status'),
    );

    // Init TTS
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);

    // Use a female voice if available
    final voices = await _tts.getVoices;
    if (voices is List) {
      final femaleVoice = voices.firstWhere(
        (v) => v['name'].toString().toLowerCase().contains('female') ||
               v['name'].toString().toLowerCase().contains('samantha') ||
               v['name'].toString().toLowerCase().contains('zira'),
        orElse: () => null,
      );
      if (femaleVoice != null) {
        await _tts.setVoice({
          'name': femaleVoice['name'],
          'locale': femaleVoice['locale'] ?? 'en-US',
        });
      }
    }

    _tts.setCompletionHandler(() {
      _isSpeaking = false;
      notifyListeners();
    });

    notifyListeners();
  }

  // ---------------------------------------------------------------
  // Speech-to-Text
  // ---------------------------------------------------------------

  Future<void> startListening({
    Function(String)? onResult,
    Duration? listenFor,
  }) async {
    if (!_speechAvailable || _isListening) return;

    _isListening = true;
    _lastWords = '';
    notifyListeners();

    await _speechToText.listen(
      onResult: (result) {
        _lastWords = result.recognizedWords;
        _confidence = result.confidence;
        notifyListeners();

        if (result.finalResult && onResult != null) {
          onResult(result.recognizedWords);
        }
      },
      listenFor: listenFor ?? const Duration(seconds: 15),
      pauseFor: const Duration(seconds: 3),
      localeId: 'en_US',
      cancelOnError: true,
      partialResults: true,
    );
  }

  Future<void> stopListening() async {
    if (!_isListening) return;

    await _speechToText.stop();
    _isListening = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------
  // Text-to-Speech
  // ---------------------------------------------------------------

  Future<void> speak(String text) async {
    if (text.isEmpty) return;

    // Clean text — remove emojis and special chars for better TTS
    final cleanText = text
        .replaceAll(RegExp(r'[✅❌📱💻🌸🔍📝⏰🎵☀️🌧️⛈️🌤️💧💨🌡️📊📦🔋⚡📶🎤⏯️⏭️⏮️▶️🔔📅📁📄💾👁️]'), '')
        .replaceAll(RegExp(r'\*\*'), '')
        .replaceAll(RegExp(r'```[^`]*```'), 'code block')
        .trim();

    if (cleanText.isEmpty) return;

    _isSpeaking = true;
    notifyListeners();

    await _tts.speak(cleanText);
  }

  Future<void> stopSpeaking() async {
    await _tts.stop();
    _isSpeaking = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------
  // Cleanup
  // ---------------------------------------------------------------

  @override
  void dispose() {
    _speechToText.stop();
    _tts.stop();
    super.dispose();
  }
}
