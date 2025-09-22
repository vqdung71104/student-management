import { useState, useEffect } from 'react'

export interface Notification {
  id: number
  title: string
  content: string
  created_at: string
  updated_at: string
}

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [skip, setSkip] = useState(0)

  const fetchNotifications = async (skipCount: number = 0, reset: boolean = false) => {
    try {
      setLoading(true)
      const response = await fetch(`http://127.0.0.1:8000/notifications?skip=${skipCount}&limit=20`)
      if (!response.ok) {
        throw new Error('Failed to fetch notifications')
      }
      const newNotifications: Notification[] = await response.json()
      
      if (reset) {
        setNotifications(newNotifications)
      } else {
        setNotifications(prev => [...prev, ...newNotifications])
      }
      
      if (newNotifications.length < 20) {
        setHasMore(false)
      }
      
      setSkip(skipCount + newNotifications.length)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchNotifications(skip)
    }
  }

  const refresh = () => {
    setSkip(0)
    setHasMore(true)
    setError(null)
    fetchNotifications(0, true)
  }

  useEffect(() => {
    fetchNotifications(0, true)
  }, [])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric'
    })
  }

  return {
    notifications,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
    formatDate
  }
}