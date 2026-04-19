/**
 * Input Validation Utilities
 * 
 * Provides validation and sanitization for user inputs
 * to prevent XSS, SQL injection, and other attacks.
 */

/**
 * Sanitize string input to prevent XSS
 */
export function sanitizeString(input: string): string {
  if (typeof input !== 'string') return ''
  
  return input
    .replace(/[<>]/g, '') // Remove < and >
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
    .slice(0, 10000) // Max length
}

/**
 * Validate query string
 */
export function validateQuery(query: string): { valid: boolean; error?: string } {
  if (!query || typeof query !== 'string') {
    return { valid: false, error: 'Query must be a non-empty string' }
  }

  const sanitized = sanitizeString(query)
  
  if (sanitized.length === 0) {
    return { valid: false, error: 'Query cannot be empty after sanitization' }
  }

  if (sanitized.length < 3) {
    return { valid: false, error: 'Query must be at least 3 characters' }
  }

  if (sanitized.length > 5000) {
    return { valid: false, error: 'Query must be less than 5000 characters' }
  }

  return { valid: true }
}

/**
 * Validate file upload
 */
export function validateFile(file: File): { valid: boolean; error?: string } {
  // Check file size (max 50MB)
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    return { valid: false, error: 'File size must be less than 50MB' }
  }

  // Check file type
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'text/markdown',
    'text/csv',
    'application/json',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ]

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: 'File type not allowed' }
  }

  // Check file name
  const fileName = file.name
  if (!/^[\w\-. ]+$/.test(fileName)) {
    return { valid: false, error: 'File name contains invalid characters' }
  }

  return { valid: true }
}

/**
 * Validate URL
 */
export function validateUrl(url: string): { valid: boolean; error?: string } {
  if (!url || typeof url !== 'string') {
    return { valid: false, error: 'URL must be a non-empty string' }
  }

  try {
    const parsed = new URL(url)
    
    // Only allow http and https
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { valid: false, error: 'Only HTTP and HTTPS protocols are allowed' }
    }

    // Block localhost and private IPs
    const hostname = parsed.hostname.toLowerCase()
    if (
      hostname === 'localhost' ||
      hostname.startsWith('127.') ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.')
    ) {
      return { valid: false, error: 'Private IP addresses are not allowed' }
    }

    return { valid: true }
  } catch {
    return { valid: false, error: 'Invalid URL format' }
  }
}

/**
 * Validate API key format
 */
export function validateApiKey(key: string): { valid: boolean; error?: string } {
  if (!key || typeof key !== 'string') {
    return { valid: false, error: 'API key must be a non-empty string' }
  }

  if (key.length < 8) {
    return { valid: false, error: 'API key must be at least 8 characters' }
  }

  if (key.length > 256) {
    return { valid: false, error: 'API key must be less than 256 characters' }
  }

  // Check for valid characters (alphanumeric, dash, underscore)
  if (!/^[\w\-]+$/.test(key)) {
    return { valid: false, error: 'API key contains invalid characters' }
  }

  return { valid: true }
}

/**
 * Sanitize object for API submission
 */
export function sanitizeObject(obj: Record<string, unknown>): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(obj)) {
    // Sanitize key
    const sanitizedKey = sanitizeString(key)
    
    if (typeof value === 'string') {
      sanitized[sanitizedKey] = sanitizeString(value)
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      sanitized[sanitizedKey] = value
    } else if (Array.isArray(value)) {
      sanitized[sanitizedKey] = value.map(item => 
        typeof item === 'string' ? sanitizeString(item) : item
      )
    } else if (value && typeof value === 'object') {
      sanitized[sanitizedKey] = sanitizeObject(value as Record<string, unknown>)
    }
  }

  return sanitized
}

/**
 * Rate limiting helper
 */
class RateLimiter {
  private requests: Map<string, number[]> = new Map()
  private readonly maxRequests: number
  private readonly windowMs: number

  constructor(maxRequests: number = 10, windowMs: number = 60000) {
    this.maxRequests = maxRequests
    this.windowMs = windowMs
  }

  check(key: string): boolean {
    const now = Date.now()
    const requests = this.requests.get(key) || []
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < this.windowMs)
    
    if (validRequests.length >= this.maxRequests) {
      return false
    }

    validRequests.push(now)
    this.requests.set(key, validRequests)
    return true
  }

  reset(key: string): void {
    this.requests.delete(key)
  }
}

export const rateLimiter = new RateLimiter(10, 60000) // 10 requests per minute

export default {
  sanitizeString,
  validateQuery,
  validateFile,
  validateUrl,
  validateApiKey,
  sanitizeObject,
  rateLimiter,
}
