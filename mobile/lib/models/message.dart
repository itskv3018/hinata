// models/message.dart
// Chat message model.

import 'package:uuid/uuid.dart';

enum MessageRole { user, assistant, system }
enum MessageStatus { sending, sent, error }

class ChatMessage {
  final String id;
  final String content;
  final MessageRole role;
  final DateTime timestamp;
  MessageStatus status;

  ChatMessage({
    String? id,
    required this.content,
    required this.role,
    DateTime? timestamp,
    this.status = MessageStatus.sent,
  })  : id = id ?? const Uuid().v4(),
        timestamp = timestamp ?? DateTime.now();

  bool get isUser => role == MessageRole.user;
  bool get isAssistant => role == MessageRole.assistant;
  bool get isSystem => role == MessageRole.system;

  Map<String, dynamic> toJson() => {
        'id': id,
        'content': content,
        'role': role.name,
        'timestamp': timestamp.toIso8601String(),
      };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
        id: json['id'],
        content: json['content'] ?? json['response'] ?? '',
        role: _parseRole(json['role'] ?? json['type'] ?? 'assistant'),
        timestamp: json['timestamp'] != null
            ? DateTime.parse(json['timestamp'])
            : DateTime.now(),
      );

  static MessageRole _parseRole(String role) {
    switch (role) {
      case 'user':
        return MessageRole.user;
      case 'assistant':
      case 'chat':
        return MessageRole.assistant;
      case 'system':
      case 'thinking':
        return MessageRole.system;
      default:
        return MessageRole.assistant;
    }
  }
}
