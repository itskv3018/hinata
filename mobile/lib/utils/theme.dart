// utils/theme.dart
// Hinata app theme — dark, purple-accented, futuristic.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class HinataTheme {
  // Brand colors
  static const Color primary = Color(0xFF9C27B0);       // Purple
  static const Color primaryLight = Color(0xFFCE93D8);   // Light purple
  static const Color primaryDark = Color(0xFF6A1B9A);    // Dark purple
  static const Color accent = Color(0xFFE040FB);         // Pink accent
  static const Color surface = Color(0xFF1A1A2E);        // Dark surface
  static const Color background = Color(0xFF0D0D1A);     // Very dark background
  static const Color card = Color(0xFF16213E);           // Card background
  static const Color userBubble = Color(0xFF7B1FA2);     // User message bubble
  static const Color botBubble = Color(0xFF1A237E);      // Bot message bubble
  static const Color textPrimary = Color(0xFFE0E0E0);
  static const Color textSecondary = Color(0xFF9E9E9E);
  static const Color success = Color(0xFF66BB6A);
  static const Color error = Color(0xFFEF5350);
  static const Color warning = Color(0xFFFFCA28);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: accent,
        surface: surface,
        error: error,
      ),
      scaffoldBackgroundColor: background,
      textTheme: GoogleFonts.poppinsTextTheme(
        ThemeData.dark().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.poppins(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
      ),
      cardTheme: const CardThemeData(
        color: card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        hintStyle: const TextStyle(color: textSecondary),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: primary,
        foregroundColor: Colors.white,
      ),
    );
  }
}
