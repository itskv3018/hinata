// screens/settings_screen.dart
// User settings – server URL, voice toggle, theme, user name.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/chat_service.dart';
import '../services/settings_service.dart';
import '../utils/theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _serverController;
  late TextEditingController _nameController;

  @override
  void initState() {
    super.initState();
    final s = context.read<SettingsService>();
    _serverController = TextEditingController(text: s.serverUrl);
    _nameController = TextEditingController(text: s.userName);
  }

  @override
  void dispose() {
    _serverController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsService>();
    final chat = context.read<ChatService>();

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D1A),
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: const Color(0xFF1A1A2E),
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Connection ──
          _sectionTitle('Connection'),
          const SizedBox(height: 8),
          _card([
            _textField(
              controller: _serverController,
              label: 'Server URL',
              hint: 'http://192.168.x.x:8000',
              icon: Icons.dns_outlined,
              onSubmitted: (v) {
                settings.setServerUrl(v);
                chat.updateServerUrl(v);
              },
            ),
            const Divider(color: Colors.white12),
            ListTile(
              leading: const Icon(Icons.wifi, color: HinataTheme.accent),
              title: const Text('Status', style: TextStyle(color: Colors.white)),
              trailing: Text(
                chat.isConnected ? 'Connected' : 'Disconnected',
                style: TextStyle(
                  color: chat.isConnected ? HinataTheme.success : Colors.redAccent,
                ),
              ),
            ),
            if (!chat.isConnected)
              Padding(
                padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
                child: ElevatedButton.icon(
                  onPressed: () async {
                    settings.setServerUrl(_serverController.text);
                    chat.updateServerUrl(_serverController.text);
                    await chat.connect();
                    if (mounted) setState(() {});
                  },
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('Reconnect'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: HinataTheme.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
          ]),

          const SizedBox(height: 24),

          // ── Voice ──
          _sectionTitle('Voice'),
          const SizedBox(height: 8),
          _card([
            SwitchListTile(
              title: const Text('Voice Enabled', style: TextStyle(color: Colors.white)),
              subtitle: Text('Talk to Hinata using your mic',
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
              value: settings.voiceEnabled,
              activeColor: HinataTheme.accent,
              onChanged: settings.setVoiceEnabled,
            ),
            const Divider(color: Colors.white12),
            SwitchListTile(
              title: const Text('Auto-Speak Replies', style: TextStyle(color: Colors.white)),
              subtitle: Text('Hinata reads responses aloud',
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
              value: settings.autoSpeak,
              activeColor: HinataTheme.accent,
              onChanged: settings.setAutoSpeak,
            ),
          ]),

          const SizedBox(height: 24),

          // ── Profile ──
          _sectionTitle('Profile'),
          const SizedBox(height: 8),
          _card([
            _textField(
              controller: _nameController,
              label: 'Your Name',
              hint: 'What should Hinata call you?',
              icon: Icons.person_outline,
              onSubmitted: settings.setUserName,
            ),
          ]),

          const SizedBox(height: 24),

          // ── About ──
          _sectionTitle('About'),
          const SizedBox(height: 8),
          _card([
            const ListTile(
              leading: Text('🌸', style: TextStyle(fontSize: 24)),
              title: Text('Hinata AI Agent', style: TextStyle(color: Colors.white)),
              subtitle: Text('Version 1.0.0',
                  style: TextStyle(color: Colors.white54, fontSize: 12)),
            ),
          ]),

          const SizedBox(height: 48),
        ],
      ),
    );
  }

  // ───────────── Helpers ─────────────

  Widget _sectionTitle(String text) {
    return Text(
      text.toUpperCase(),
      style: TextStyle(
        color: HinataTheme.accent.withOpacity(0.8),
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 1.4,
      ),
    );
  }

  Widget _card(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: HinataTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: Column(children: children),
    );
  }

  Widget _textField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    required ValueChanged<String> onSubmitted,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: TextField(
        controller: controller,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          prefixIcon: Icon(icon, color: HinataTheme.accent, size: 20),
          labelText: label,
          labelStyle: TextStyle(color: Colors.white.withOpacity(0.5)),
          hintText: hint,
          hintStyle: TextStyle(color: Colors.white.withOpacity(0.2)),
          border: InputBorder.none,
        ),
        onSubmitted: onSubmitted,
      ),
    );
  }
}
