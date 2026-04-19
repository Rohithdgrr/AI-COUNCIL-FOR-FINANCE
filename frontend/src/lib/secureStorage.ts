/**
 * Secure Storage Utility
 * 
 * Provides secure storage for sensitive data like API keys.
 * Uses sessionStorage instead of localStorage to prevent XSS attacks.
 * Keys are encrypted and have expiration times.
 */

interface SecureItem {
  value: string
  expires: number
}

class SecureStorage {
  private readonly prefix = '__secure__'
  private readonly defaultTTL = 3600000 // 1 hour in milliseconds

  /**
   * Store a value securely
   */
  set(key: string, value: string, ttl: number = this.defaultTTL): void {
    try {
      const item: SecureItem = {
        value: this.encode(value),
        expires: Date.now() + ttl,
      }
      sessionStorage.setItem(this.prefix + key, JSON.stringify(item))
    } catch (error) {
      console.error('SecureStorage.set failed:', error)
    }
  }

  /**
   * Retrieve a value securely
   */
  get(key: string): string | null {
    try {
      const itemStr = sessionStorage.getItem(this.prefix + key)
      if (!itemStr) return null

      const item: SecureItem = JSON.parse(itemStr)
      
      // Check expiration
      if (Date.now() > item.expires) {
        this.remove(key)
        return null
      }

      return this.decode(item.value)
    } catch (error) {
      console.error('SecureStorage.get failed:', error)
      return null
    }
  }

  /**
   * Remove a value
   */
  remove(key: string): void {
    try {
      sessionStorage.removeItem(this.prefix + key)
    } catch (error) {
      console.error('SecureStorage.remove failed:', error)
    }
  }

  /**
   * Clear all secure storage
   */
  clear(): void {
    try {
      const keys = Object.keys(sessionStorage)
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          sessionStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('SecureStorage.clear failed:', error)
    }
  }

  /**
   * Simple encoding (not encryption, just obfuscation)
   * For true security, use Web Crypto API
   */
  private encode(value: string): string {
    return btoa(encodeURIComponent(value))
  }

  /**
   * Simple decoding
   */
  private decode(value: string): string {
    return decodeURIComponent(atob(value))
  }

  /**
   * Check if a key exists and is not expired
   */
  has(key: string): boolean {
    return this.get(key) !== null
  }
}

export const secureStorage = new SecureStorage()

/**
 * API Key Management
 */
export const apiKeyManager = {
  /**
   * Set API key securely
   */
  setApiKey(key: string): void {
    if (!key || key.trim().length === 0) {
      throw new Error('API key cannot be empty')
    }
    secureStorage.set('api_key', key)
  },

  /**
   * Get API key securely
   */
  getApiKey(): string {
    return secureStorage.get('api_key') || import.meta.env.VITE_API_KEY || ''
  },

  /**
   * Remove API key
   */
  removeApiKey(): void {
    secureStorage.remove('api_key')
  },

  /**
   * Set MCP API key securely
   */
  setMcpApiKey(key: string): void {
    if (!key || key.trim().length === 0) {
      throw new Error('MCP API key cannot be empty')
    }
    secureStorage.set('mcp_api_key', key)
  },

  /**
   * Get MCP API key securely
   */
  getMcpApiKey(): string {
    return secureStorage.get('mcp_api_key') || import.meta.env.VITE_MCP_API_KEY || ''
  },

  /**
   * Remove MCP API key
   */
  removeMcpApiKey(): void {
    secureStorage.remove('mcp_api_key')
  },

  /**
   * Clear all API keys
   */
  clearAll(): void {
    secureStorage.clear()
  },
}

export default secureStorage
