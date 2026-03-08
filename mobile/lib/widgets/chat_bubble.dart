// widgets/chat_bubble.dart
// Styled chat bubble for user and assistant messages.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/message.dart';
import '../utils/theme.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final bool showAvatar;

  const ChatBubble({
    super.key,
    required this.message,
    this.showAvatar = true,
  });

  bool get _isUser => message.role == MessageRole.user;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        top: showAvatar ? 12 : 2,
        bottom: 2,
        left: _isUser ? 48 : 0,
        right: _isUser ? 0 : 48,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment:
            _isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!_isUser && showAvatar) _avatar() else if (!_isUser) const SizedBox(width: 36),
          const SizedBox(width: 8),
          Flexible(child: _bubble(context)),
          if (_isUser) const SizedBox(width: 4),
        ],
      ),
    );
  }

  Widget _avatar() {
    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [HinataTheme.primary, HinataTheme.accent],
        ),
        boxShadow: [
          BoxShadow(
            color: HinataTheme.primary.withOpacity(0.25),
            blurRadius: 8,
          ),
        ],
      ),
      child: const Center(
        child: Text('🌸', style: TextStyle(fontSize: 14)),
      ),
    );
  }

  Widget _bubble(BuildContext context) {
    final isLoading = message.status == MessageStatus.loading;

    return GestureDetector(
      onLongPress: () {
        Clipboard.setData(ClipboardData(text: message.content));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Copied to clipboard'),
            duration: Duration(seconds: 1),
            behavior: SnackBarBehavior.floating,
          ),
        );
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: _isUser
              ? HinataTheme.primary.withOpacity(0.25)
              : HinataTheme.surface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(_isUser ? 16 : 4),
            bottomRight: Radius.circular(_isUser ? 4 : 16),
          ),
          border: Border.all(
            color: _isUser
                ? HinataTheme.primary.withOpacity(0.3)
                : Colors.white.withOpacity(0.06),
          ),
        ),
        child: isLoading
            ? _typingIndicator()
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SelectableText(
                    message.content,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 14,
                      height: 1.45,
                    ),
                  ),
                  if (message.status == MessageStatus.error)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.error_outline,
                              size: 12, color: Colors.redAccent.withOpacity(0.7)),
                          const SizedBox(width: 4),
                          Text(
                            'Failed to send',
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.redAccent.withOpacity(0.7),
                            ),
                          ),
                        ],
                      ),
                    ),
                  // Timestamp
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      _formatTime(message.timestamp),
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.white.withOpacity(0.25),
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _typingIndicator() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) {
        return TweenAnimationBuilder<double>(
          tween: Tween(begin: 0.3, end: 1.0),
          duration: Duration(milliseconds: 600 + i * 200),
          builder: (_, v, child) => Opacity(opacity: v, child: child),
          child: Container(
            margin: EdgeInsets.only(right: i < 2 ? 4 : 0),
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: HinataTheme.accent.withOpacity(0.6),
            ),
          ),
        );
      }),
    );
  }

  String _formatTime(DateTime dt) {
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}
