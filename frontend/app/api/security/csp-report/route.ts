/**
 * CSP Violation Report API Route
 * Receives Content Security Policy violation reports
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const report = await request.json();

    // Log CSP violation
    console.warn('[CSP VIOLATION]', {
      documentURI: report['document-uri'],
      violatedDirective: report['violated-directive'],
      blockedURI: report['blocked-uri'],
      effectiveDirective: report['effective-directive'],
      originalPolicy: report['original-policy'],
      sourceFile: report['source-file'],
      lineNumber: report['line-number'],
      columnNumber: report['column-number'],
    });

    // In production, aggregate and analyze CSP violations
    // This helps identify:
    // 1. Legitimate resources that need to be whitelisted
    // 2. Actual XSS attempts
    // 3. Browser extensions causing violations

    // TODO: Send to monitoring service
    // await sendToMonitoring(report);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to process CSP report:', error);
    return NextResponse.json(
      { error: 'Failed to process report' },
      { status: 500 }
    );
  }
}
