// screens/home_screen.dart
// Main chat interface with voice activation and plugin access.

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';

import '../models/message.dart';
import '../services/chat_service.dart';
import '../services/voice_service.dart';
import '../services/settings_service.dart';
import '../utils/theme.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/message_input.dart';
import '../widgets/voice_button.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final ScrollController _scrollController = ScrollController();
  bool _showScrollDown = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final show = _scrollController.hasClients &&
        _scrollController.offset <
            _scrollController.position.maxScrollExtent - 100;
    if (show != _showScrollDown) {
      setState(() => _showScrollDown = show);
    }
  }

  void _scrollToBottom({bool animate = true}) {
    if (!_scrollController.hasClients) return;
    final target = _scrollController.position.maxScrollExtent;
    if (animate) {
      _scrollController.animateTo(target,
          duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    } else {
      _scrollController.jumpTo(target);
    }
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    final chat = context.read<ChatService>();
    final voice = context.read<VoiceService>();
    final settings = context.read<SettingsService>();

    chat.addMessage(ChatMessage.user(text));
    _scrollToBottom();

    final response = await chat.sendMessage(text);

    if (settings.autoSpeak && response != null) {
      voice.speak(response);
    }

    _scrollToBottom();
  }

  Future<void> _onVoiceResult(String transcript) async {
    if (transcript.isNotEmpty) {
      await _sendMessage(transcript);
    }
  }

  @override
  Widget build(BuildContext context) {
    final chat = context.watch<ChatService>();
    final voice = context.watch<VoiceService>();

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF1A1A2E), Color(0xFF0D0D1A)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // ─── Top bar ───
              _buildTopBar(chat),

              // ─── Messages ───
              Expanded(
                child: Stack(
                  children: [
                    chat.messages.isEmpty
                        ? _buildEmptyState()
                        : _buildMessageList(chat.messages),
                    if (_showScrollDown)
                      Positioned(
                        bottom: 8,
                        right: 16,
                        child: _buildScrollDownFab(),
                      ),
                  ],
                ),
              ),

              // ─── Listening overlay ───
              if (voice.isListening) _buildListeningBanner(),

              // ─── Input area ───
              MessageInput(
                onSend: _sendMessage,
                isLoading: chat.isLoading,
              ),
            ],
          ),
        ),
      ),

      // Voice FAB
      floatingActionButton: VoiceButton(
        isListening: voice.isListening,
        onPressed: () async {
          if (voice.isListening) {
            voice.stopListening();
          } else {
            await voice.startListening(_onVoiceResult);
          }
        },
      ),
    );
  }

  // ────────────────────── Sub-Widgets ──────────────────────

  Widget _buildTopBar(ChatService chat) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          // Avatar
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                colors: [HinataTheme.primary, HinataTheme.accent],
              ),
              boxShadow: [
                BoxShadow(
                  color: HinataTheme.primary.withOpacity(0.3),
                  blurRadius: 10,
                ),
              ],
            ),
            child: const Center(
              child: Text('🌸', style: TextStyle(fontSize: 20)),
            ),
          ),

          const SizedBox(width: 12),

          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Hinata',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                chat.isConnected ? 'Online' : 'Offline',
                style: TextStyle(
                  color: chat.isConnected
                      ? HinataTheme.success
                      : Colors.white.withOpacity(0.4),
                  fontSize: 12,
                ),
              ),
            ],
          ),

          const Spacer(),

          // Connection indicator
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: chat.isConnected ? HinataTheme.success : Colors.red,
            ),
          ),

          const SizedBox(width: 12),

          // Settings
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Colors.white70),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: HinataTheme.primary.withOpacity(0.1),
            ),
            child: const Center(
              child: Text('🌸', style: TextStyle(fontSize: 36)),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Hey! I\'m Hinata',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Ask me anything or tap the mic to talk',
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              _quickAction('What can you do?'),
              _quickAction('Open YouTube'),
              _quickAction('Take a screenshot'),
              _quickAction('Set a reminder'),
            ],
          ),
        ],
      ).animate().fadeIn(duration: 600.ms),
    );
  }

  Widget _quickAction(String text) {
    return ActionChip(
      label: Text(text, style: const TextStyle(fontSize: 12)),
      backgroundColor: HinataTheme.surface,
      labelStyle: const TextStyle(color: Colors.white70),
      side: BorderSide(color: HinataTheme.primary.withOpacity(0.3)),
      onPressed: () => _sendMessage(text),
    );
  }

  Widget _buildMessageList(List<ChatMessage> messages) {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: messages.length,
      itemBuilder: (context, i) {
        final msg = messages[i];
        return ChatBubble(
          message: msg,
          showAvatar: i == 0 || messages[i - 1].role != msg.role,
        ).animate().fadeIn(duration: 200.ms).slideX(
              begin: msg.role == MessageRole.user ? 0.1 : -0.1,
              end: 0,
              duration: 200.ms,
            );
      },
    );
  }

  Widget _buildScrollDownFab() {
    return FloatingActionButton.small(
      backgroundColor: HinataTheme.surface,
      onPressed: _scrollToBottom,
      child: const Icon(Icons.keyboard_arrow_down, color: Colors.white70),
    );
  }

  Widget _buildListeningBanner() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: HinataTheme.primary.withOpacity(0.15),
      child: Row(
        children: [
          const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation(HinataTheme.accent),
            ),
          ),
          const SizedBox(width: 12),
          const Text(
            'Listening...',
            style: TextStyle(color: Colors.white70, fontSize: 13),
          ),
          const Spacer(),
          TextButton(
            onPressed: () => context.read<VoiceService>().stopListening(),
            child: const Text('Cancel', style: TextStyle(color: HinataTheme.accent)),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 200.ms);
  }
}
