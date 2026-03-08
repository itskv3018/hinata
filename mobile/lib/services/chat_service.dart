// services/chat_service.dart
// Manages WebSocket connection to the Hinata backend and chat state.

import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../models/message.dart';
import '../utils/constants.dart';

class ChatService extends ChangeNotifier {
  final List<ChatMessage> _messages = [];
  WebSocketChannel? _channel;
  bool _isConnected = false;
  bool _isThinking = false;
  String _serverUrl = AppConstants.defaultServerUrl;
  String _wsUrl = AppConstants.defaultWsUrl;
  String _userId = const Uuid().v4().substring(0, 8);
  StreamSubscription? _subscription;

  // Getters
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isConnected => _isConnected;
  bool get isThinking => _isThinking;
  String get serverUrl => _serverUrl;
  String get userId => _userId;

  // ---------------------------------------------------------------
  // Connection
  // ---------------------------------------------------------------

  void setServerUrl(String url) {
    _serverUrl = url.replaceAll(RegExp(r'/+$'), '');
    _wsUrl = _serverUrl.replaceFirst('http', 'ws') + '/ws';
    notifyListeners();
  }

  Future<void> connect() async {
    if (_isConnected) return;

    try {
      final wsUri = Uri.parse('$_wsUrl/$_userId');
      _channel = WebSocketChannel.connect(wsUri);

      _subscription = _channel!.stream.listen(
        (data) => _onMessage(data),
        onError: (error) => _onError(error),
        onDone: () => _onDisconnected(),
      );

      _isConnected = true;
      notifyListeners();
      print('🌸 Connected to Hinata server');
    } catch (e) {
      print('❌ Connection failed: $e');
      _isConnected = false;
      notifyListeners();
    }
  }

  void disconnect() {
    _subscription?.cancel();
    _channel?.sink.close();
    _isConnected = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------
  // Messaging
  // ---------------------------------------------------------------

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message to chat
    final userMsg = ChatMessage(
      content: text,
      role: MessageRole.user,
    );
    _messages.add(userMsg);
    _isThinking = true;
    notifyListeners();

    if (_isConnected && _channel != null) {
      // Send via WebSocket
      _channel!.sink.add(jsonEncode({'message': text}));
    } else {
      // Fallback: send via REST API
      await _sendViaHttp(text);
    }
  }

  Future<void> _sendViaHttp(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'message': text,
          'user_id': _userId,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final botMsg = ChatMessage(
          content: data['response'] ?? 'No response',
          role: MessageRole.assistant,
        );
        _messages.add(botMsg);
      } else {
        _messages.add(ChatMessage(
          content: '❌ Server error: ${response.statusCode}',
          role: MessageRole.system,
        ));
      }
    } catch (e) {
      _messages.add(ChatMessage(
        content: '❌ Could not reach server. Make sure Hinata backend is running.\n\nError: $e',
        role: MessageRole.system,
      ));
    }

    _isThinking = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------
  // WebSocket handlers
  // ---------------------------------------------------------------

  void _onMessage(dynamic data) {
    try {
      final json = jsonDecode(data as String);
      final type = json['type'] ?? 'chat';

      if (type == 'thinking') {
        _isThinking = true;
        notifyListeners();
        return;
      }

      _isThinking = false;

      final msg = ChatMessage(
        content: json['response'] ?? json['message'] ?? '',
        role: type == 'system' ? MessageRole.system : MessageRole.assistant,
      );
      _messages.add(msg);
      notifyListeners();
    } catch (e) {
      print('Error parsing message: $e');
    }
  }

  void _onError(dynamic error) {
    print('WebSocket error: $error');
    _isConnected = false;
    _isThinking = false;
    notifyListeners();
  }

  void _onDisconnected() {
    print('WebSocket disconnected');
    _isConnected = false;
    _isThinking = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------
  // Utils
  // ---------------------------------------------------------------

  void clearMessages() {
    _messages.clear();
    notifyListeners();
  }

  Future<bool> checkServerHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$_serverUrl/health'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<List<Map<String, dynamic>>> getPlugins() async {
    try {
      final response = await http.get(Uri.parse('$_serverUrl/plugins'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['plugins'] ?? []);
      }
    } catch (e) {
      print('Error fetching plugins: $e');
    }
    return [];
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
