// widgets/voice_button.dart
// Floating mic button with pulse animation when listening.

import 'package:flutter/material.dart';

import '../utils/theme.dart';

class VoiceButton extends StatefulWidget {
  final bool isListening;
  final VoidCallback onPressed;

  const VoiceButton({
    super.key,
    required this.isListening,
    required this.onPressed,
  });

  @override
  State<VoiceButton> createState() => _VoiceButtonState();
}

class _VoiceButtonState extends State<VoiceButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseCtrl;
  late Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _pulseAnim = Tween(begin: 1.0, end: 1.25).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(covariant VoiceButton old) {
    super.didUpdateWidget(old);
    if (widget.isListening && !_pulseCtrl.isAnimating) {
      _pulseCtrl.repeat(reverse: true);
    } else if (!widget.isListening && _pulseCtrl.isAnimating) {
      _pulseCtrl.stop();
      _pulseCtrl.reset();
    }
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnim,
      builder: (_, child) {
        final scale = widget.isListening ? _pulseAnim.value : 1.0;
        return Transform.scale(scale: scale, child: child);
      },
      child: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            colors: widget.isListening
                ? [Colors.redAccent, Colors.red.shade700]
                : [HinataTheme.primary, HinataTheme.accent],
          ),
          boxShadow: [
            BoxShadow(
              color: (widget.isListening ? Colors.redAccent : HinataTheme.primary)
                  .withOpacity(0.4),
              blurRadius: 16,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(28),
            onTap: widget.onPressed,
            child: Icon(
              widget.isListening ? Icons.stop_rounded : Icons.mic_rounded,
              color: Colors.white,
              size: 26,
            ),
          ),
        ),
      ),
    );
  }
}
