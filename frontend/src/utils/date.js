import { formatDistanceToNow, format, parseISO } from 'date-fns'

export function formatDate(dateString) {
  if (!dateString) return ''
  return format(parseISO(dateString), 'MMM dd, yyyy')
}

export function formatDateTime(dateString) {
  if (!dateString) return ''
  return format(parseISO(dateString), 'MMM dd, yyyy HH:mm')
}

export function formatRelative(dateString) {
  if (!dateString) return ''
  return formatDistanceToNow(parseISO(dateString), { addSuffix: true })
}

export function isDueSoon(dueDate) {
  if (!dueDate) return false
  const now = new Date()
  const due = parseISO(dueDate)
  const diffDays = (due - now) / (1000 * 60 * 60 * 24)
  return diffDays <= 7 && diffDays >= 0
}

export function isDueToday(dueDate) {
  if (!dueDate) return false
  const now = new Date()
  const due = parseISO(dueDate)
  return format(now, 'yyyy-MM-dd') === format(due, 'yyyy-MM-dd')
}
