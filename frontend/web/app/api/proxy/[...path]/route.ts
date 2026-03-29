import { NextRequest, NextResponse } from 'next/server';

/**
 * API Proxy Route
 *
 * This route acts as a secure proxy between the frontend and the Phase 2 REST API.
 * It injects the API secret key securely (never exposed to client) and handles
 * authentication headers.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const API_SECRET_KEY = process.env.API_SECRET_KEY;
const API_TIMEOUT = parseInt(process.env.API_TIMEOUT || '30000', 10);

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const pathSegments = await params;
    const path = pathSegments.path.join('/');
    const url = new URL(`${API_BASE_URL}/${path}`);

    // Preserve query parameters
    url.search = request.nextUrl.search;

    const headers = new Headers({
      'Content-Type': 'application/json',
    });

    // Add API key if configured
    if (API_SECRET_KEY) {
      headers.set('X-API-Key', API_SECRET_KEY);
    }

    // Forward auth headers if present
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.set('Authorization', authHeader);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers,
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          {
            error: data.error || 'API Error',
            status: response.status,
          },
          { status: response.status }
        );
      }

      return NextResponse.json(data);
    } finally {
      clearTimeout(timeoutId);
    }
  } catch (error) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from API' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const pathSegments = await params;
    const path = pathSegments.path.join('/');
    const url = new URL(`${API_BASE_URL}/${path}`);

    const contentType = request.headers.get('content-type') || '';
    const headers = new Headers();

    if (API_SECRET_KEY) {
      headers.set('X-API-Key', API_SECRET_KEY);
    }

    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.set('Authorization', authHeader);
    }

    let body: BodyInit;

    // Handle multipart/form-data for file uploads
    if (contentType.includes('multipart/form-data')) {
      // Pass FormData directly without Content-Type header
      // The browser will set it with the boundary
      const formData = await request.formData();
      body = formData;
    } else {
      // Handle JSON requests
      headers.set('Content-Type', 'application/json');
      const jsonBody = await request.json();
      body = JSON.stringify(jsonBody);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(url.toString(), {
        method: 'POST',
        headers,
        body,
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          {
            error: data.error || 'API Error',
            status: response.status,
          },
          { status: response.status }
        );
      }

      return NextResponse.json(data);
    } finally {
      clearTimeout(timeoutId);
    }
  } catch (error) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from API' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const pathSegments = await params;
    const path = pathSegments.path.join('/');
    const url = new URL(`${API_BASE_URL}/${path}`);

    const contentType = request.headers.get('content-type') || '';
    const headers = new Headers();

    if (API_SECRET_KEY) {
      headers.set('X-API-Key', API_SECRET_KEY);
    }

    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.set('Authorization', authHeader);
    }

    let body: BodyInit;

    // Handle multipart/form-data for file uploads
    if (contentType.includes('multipart/form-data')) {
      // Pass FormData directly without Content-Type header
      const formData = await request.formData();
      body = formData;
    } else {
      // Handle JSON requests
      headers.set('Content-Type', 'application/json');
      const jsonBody = await request.json();
      body = JSON.stringify(jsonBody);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(url.toString(), {
        method: 'PUT',
        headers,
        body,
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          {
            error: data.error || 'API Error',
            status: response.status,
          },
          { status: response.status }
        );
      }

      return NextResponse.json(data);
    } finally {
      clearTimeout(timeoutId);
    }
  } catch (error) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from API' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const pathSegments = await params;
    const path = pathSegments.path.join('/');
    const url = new URL(`${API_BASE_URL}/${path}`);

    const headers = new Headers({
      'Content-Type': 'application/json',
    });

    if (API_SECRET_KEY) {
      headers.set('X-API-Key', API_SECRET_KEY);
    }

    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.set('Authorization', authHeader);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(url.toString(), {
        method: 'DELETE',
        headers,
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          {
            error: data.error || 'API Error',
            status: response.status,
          },
          { status: response.status }
        );
      }

      return NextResponse.json(data);
    } finally {
      clearTimeout(timeoutId);
    }
  } catch (error) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from API' },
      { status: 500 }
    );
  }
}
