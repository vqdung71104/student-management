import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import './Schedule.css'

interface ClassSchedule {
  id: string
  class_name: string
  subject_name: string
  subject_id: string
  study_date: string
  study_time_start: string
  study_time_end: string
  classroom: string
  study_week: string
  teacher_name: string
  day_of_week: number
}

interface PositionedClass extends ClassSchedule {
  start_minutes: number
  end_minutes: number
  column_index: number
  total_columns: number
  conflict_group_id: string
  conflict_size: number
}

interface ConflictGroup {
  id: string
  day_of_week: number
  start_minutes: number
  end_minutes: number
  classes: PositionedClass[]
}

const Schedule = () => {
  const { userInfo } = useAuth()
  const [classes, setClasses] = useState<ClassSchedule[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)

  const getAuthRequestOptions = (options: RequestInit = {}): RequestInit => {
    const token = localStorage.getItem('access_token')
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    return {
      ...options,
      credentials: 'include',
      headers,
    }
  }

  const daysOfWeek = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  const daysOfWeekFull = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']

  // Time slots from 6:00 to 18:00
  const timeSlots: string[] = []
  for (let hour = 6; hour <= 18; hour++) {
    timeSlots.push(`${hour.toString().padStart(2, '0')}:00`)
  }

  useEffect(() => {
    fetchSchedule()
  }, [])

  const fetchSchedule = async () => {
    setLoading(true)
    try {
      if (!userInfo?.id) {
        setLoading(false)
        return
      }

      const classRegisterResponse = await fetch(`/api/class-registers/student/${userInfo.id}`, getAuthRequestOptions())

      if (classRegisterResponse.ok) {
        const classRegisters = await classRegisterResponse.json()

        const classDetails = await Promise.all(
          classRegisters.map(async (register: any) => {
            try {
              const classResponse = await fetch(`/api/classes/${register.class_id}`, getAuthRequestOptions())
              if (classResponse.ok) {
                const classData = await classResponse.json()
                const subjectData = classData.subject

                const dayMap: { [key: string]: number } = {
                  'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                  'Thursday': 4, 'Friday': 5, 'Saturday': 6
                }

                const scheduleEntries = []

                if (classData.study_date && classData.study_date.includes(',')) {
                  const days = classData.study_date.split(',').map((d: string) => d.trim())

                  for (const dayName of days) {
                    const dayOfWeek = dayMap[dayName] || 1

                    scheduleEntries.push({
                      id: `${register.id}-${dayName}`,
                      class_name: classData.class_name,
                      subject_name: subjectData.subject_name,
                      subject_id: subjectData.subject_id,
                      study_date: dayName,
                      study_time_start: classData.study_time_start || '07:00:00',
                      study_time_end: classData.study_time_end || '08:50:00',
                      classroom: classData.classroom || 'Chưa phân phòng',
                      study_week: Array.isArray(classData.study_week) ? classData.study_week.join(', ') : (classData.study_week || 'Chưa xác định'),
                      teacher_name: classData.teacher_name || 'Chưa phân công',
                      day_of_week: dayOfWeek
                    })
                  }
                } else {
                  let dayOfWeek = 1
                  if (classData.study_date) {
                    if (classData.study_date.includes('-')) {
                      const studyDate = new Date(classData.study_date)
                      dayOfWeek = studyDate.getDay()
                    } else {
                      dayOfWeek = dayMap[classData.study_date] || 1
                    }
                  }

                  scheduleEntries.push({
                    id: register.id,
                    class_name: classData.class_name,
                    subject_name: subjectData.subject_name,
                    subject_id: subjectData.subject_id,
                    study_date: classData.study_date,
                    study_time_start: classData.study_time_start || '07:00:00',
                    study_time_end: classData.study_time_end || '08:50:00',
                    classroom: classData.classroom || 'Chưa phân phòng',
                    study_week: Array.isArray(classData.study_week) ? classData.study_week.join(', ') : (classData.study_week || 'Chưa xác định'),
                    teacher_name: classData.teacher_name || 'Chưa phân công',
                    day_of_week: dayOfWeek
                  })
                }

                return scheduleEntries
              }
            } catch (error) {
              console.error('Error fetching class details:', error)
            }
            return null
          })
        )

        const flattenedClasses = classDetails.flat().filter(item => item !== null)
        setClasses(flattenedClasses)
      } else {
        setClasses([])
      }
    } catch (error) {
      console.error('Error fetching schedule:', error)
      setClasses([])
    }
    setLoading(false)
  }


  const toMinutes = (timeString: string) => {
    if (!timeString) return 0
    const [hourStr, minuteStr] = timeString.split(':')
    return parseInt(hourStr || '0') * 60 + parseInt(minuteStr || '0')
  }

  const calculateClassPosition = (classItem: { study_time_start: string; study_time_end: string }) => {
    const startHour = parseInt(classItem.study_time_start.split(':')[0])
    const startMinute = parseInt(classItem.study_time_start.split(':')[1])
    const endHour = parseInt(classItem.study_time_end.split(':')[0])
    const endMinute = parseInt(classItem.study_time_end.split(':')[1])

    // Calculate position from 6:00 (base hour)
    const baseHour = 6
    const topPosition = ((startHour - baseHour) * 60 + startMinute) / 60 // in hours
    const duration = ((endHour * 60 + endMinute) - (startHour * 60 + startMinute)) / 60 // in hours

    return {
      top: `${topPosition * 60}px`, // 60px per hour
      height: `${duration * 60}px`
    }
  }

  const formatTime = (timeString: string) => {
    if (!timeString) return ''
    return timeString.slice(0, 5)
  }

  const scheduleLayout = useMemo(() => {
    const classesByDay = new Map<number, ClassSchedule[]>()
    for (const cls of classes) {
      const dayList = classesByDay.get(cls.day_of_week) || []
      dayList.push(cls)
      classesByDay.set(cls.day_of_week, dayList)
    }

    const positionedByDay = new Map<number, PositionedClass[]>()
    const conflictGroups: ConflictGroup[] = []

    for (const [dayOfWeek, dayClasses] of classesByDay.entries()) {
      const sorted = [...dayClasses].sort((a, b) => {
        const diff = toMinutes(a.study_time_start) - toMinutes(b.study_time_start)
        if (diff !== 0) return diff
        return toMinutes(a.study_time_end) - toMinutes(b.study_time_end)
      })

      const rawGroups: { start: number; end: number; classes: ClassSchedule[] }[] = []
      for (const cls of sorted) {
        const start = toMinutes(cls.study_time_start)
        const end = toMinutes(cls.study_time_end)
        const lastGroup = rawGroups[rawGroups.length - 1]

        if (!lastGroup || start >= lastGroup.end) {
          rawGroups.push({
            start,
            end,
            classes: [cls]
          })
        } else {
          lastGroup.classes.push(cls)
          lastGroup.end = Math.max(lastGroup.end, end)
        }
      }

      const dayPositioned: PositionedClass[] = []

      rawGroups.forEach((group, groupIndex) => {
        const groupId = `conflict-${dayOfWeek}-${groupIndex}-${group.start}-${group.end}`
        const columnEnds: number[] = []
        const positionedInGroup: PositionedClass[] = []

        const groupSorted = [...group.classes].sort((a, b) => {
          const diff = toMinutes(a.study_time_start) - toMinutes(b.study_time_start)
          if (diff !== 0) return diff
          return toMinutes(a.study_time_end) - toMinutes(b.study_time_end)
        })

        for (const cls of groupSorted) {
          const start = toMinutes(cls.study_time_start)
          const end = toMinutes(cls.study_time_end)

          let columnIndex = columnEnds.findIndex((currentEnd) => start >= currentEnd)
          if (columnIndex === -1) {
            columnIndex = columnEnds.length
            columnEnds.push(end)
          } else {
            columnEnds[columnIndex] = end
          }

          positionedInGroup.push({
            ...cls,
            start_minutes: start,
            end_minutes: end,
            column_index: columnIndex,
            total_columns: 1,
            conflict_group_id: groupId,
            conflict_size: group.classes.length
          })
        }

        const totalColumns = Math.max(columnEnds.length, 1)
        const finalized = positionedInGroup.map((item) => ({
          ...item,
          total_columns: totalColumns
        }))

        dayPositioned.push(...finalized)
        conflictGroups.push({
          id: groupId,
          day_of_week: dayOfWeek,
          start_minutes: group.start,
          end_minutes: group.end,
          classes: finalized
        })
      })

      positionedByDay.set(dayOfWeek, dayPositioned)
    }

    return {
      positionedByDay,
      conflictGroups
    }
  }, [classes])

  const conflictGroupsOnly = useMemo(
    () => scheduleLayout.conflictGroups.filter((group) => group.classes.length > 1),
    [scheduleLayout.conflictGroups]
  )

  const selectedGroup = useMemo(
    () => scheduleLayout.conflictGroups.find((group) => group.id === selectedGroupId) || null,
    [scheduleLayout.conflictGroups, selectedGroupId]
  )

  useEffect(() => {
    if (selectedGroupId && !scheduleLayout.conflictGroups.some((group) => group.id === selectedGroupId)) {
      setSelectedGroupId(null)
    }
  }, [scheduleLayout.conflictGroups, selectedGroupId])

  const formatMinuteToTime = (minutes: number) => {
    const hour = Math.floor(minutes / 60)
    const minute = minutes % 60
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
  }

  const subjectColorPalette = [
    { blockClass: 'bg-blue-400', solidColor: '#3b82f6', softColor: '#eff6ff' },
    { blockClass: 'bg-green-400', solidColor: '#22c55e', softColor: '#f0fdf4' },
    { blockClass: 'bg-purple-400', solidColor: '#a855f7', softColor: '#faf5ff' },
    { blockClass: 'bg-pink-400', solidColor: '#ec4899', softColor: '#fdf2f8' },
    { blockClass: 'bg-yellow-400', solidColor: '#f59e0b', softColor: '#fffbeb' },
    { blockClass: 'bg-indigo-400', solidColor: '#6366f1', softColor: '#eef2ff' },
    { blockClass: 'bg-red-400', solidColor: '#ef4444', softColor: '#fef2f2' },
    { blockClass: 'bg-teal-400', solidColor: '#14b8a6', softColor: '#f0fdfa' }
  ]

  const subjectColorMap = useMemo(() => {
    const uniqueSubjectIds = Array.from(
      new Set(classes.map((item) => (item.subject_id || 'UNKNOWN').trim() || 'UNKNOWN'))
    ).sort()

    const map = new Map<string, (typeof subjectColorPalette)[number]>()
    uniqueSubjectIds.forEach((subjectId, index) => {
      map.set(subjectId, subjectColorPalette[index % subjectColorPalette.length])
    })
    return map
  }, [classes])

  const getSubjectColor = (subjectId: string) => {
    const key = (subjectId || 'UNKNOWN').trim() || 'UNKNOWN'
    return subjectColorMap.get(key) || subjectColorPalette[0]
  }

  const totalSubjects = subjectColorMap.size

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Thời khóa biểu</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Tổng lớp học</div>
          <div className="text-2xl font-bold text-gray-900">{classes.length}</div>
        </div>
        <div className="bg-white rounded-lg border border-blue-300 p-4">
          <div className="text-sm text-blue-700">Tổng học phần</div>
          <div className="text-2xl font-bold text-blue-700">{totalSubjects}</div>
        </div>
        <div className="bg-white rounded-lg border border-amber-300 p-4">
          <div className="text-sm text-amber-700">Cụm xung đột lịch</div>
          <div className="text-2xl font-bold text-amber-700">{conflictGroupsOnly.length}</div>
        </div>
        <div className="bg-white rounded-lg border border-red-300 p-4">
          <div className="text-sm text-red-700">Lớp bị xung đột</div>
          <div className="text-2xl font-bold text-red-700">
            {conflictGroupsOnly.reduce((sum, group) => sum + group.classes.length, 0)}
          </div>
        </div>
      </div>

      {/* Timetable View */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <div className="timetable-container">
            {/* Header with days */}
            <div className="timetable-header">
              <div className="time-column-header"></div>
              {daysOfWeek.map((day) => (
                <div key={day} className="day-header">
                  <div className="day-name">{day}</div>
                </div>
              ))}
            </div>

            {/* Time grid */}
            <div className="timetable-grid">
              {/* Time column */}
              <div className="time-column">
                {timeSlots.map(time => (
                  <div key={time} className="time-slot">
                    {time}
                  </div>
                ))}
              </div>

              {/* Day columns */}
              {[0, 1, 2, 3, 4, 5, 6].map(dayIndex => (
                <div key={dayIndex} className="day-column">
                  {/* Grid lines */}
                  {timeSlots.map(time => (
                    <div key={time} className="grid-cell"></div>
                  ))}

                  {/* Classes positioned absolutely */}
                  <div className="classes-container">
                    {(scheduleLayout.positionedByDay.get(dayIndex) || [])
                      .sort((a, b) => a.start_minutes - b.start_minutes)
                      .map((classItem) => {
                        const position = calculateClassPosition(classItem)
                        const colorClass = getSubjectColor(classItem.subject_id).blockClass
                        const widthPercent = 100 / Math.max(classItem.total_columns, 1)
                        const leftPercent = classItem.column_index * widthPercent
                        const isConflict = classItem.conflict_size > 1

                        return (
                          <div
                            key={classItem.id}
                            className={`class-block ${colorClass} ${isConflict ? 'class-block-conflict' : ''} ${selectedGroupId === classItem.conflict_group_id ? 'class-block-selected' : ''}`}
                            style={{
                              top: position.top,
                              height: position.height,
                              left: `calc(${leftPercent}% + 4px)`,
                              width: `calc(${widthPercent}% - 8px)`
                            }}
                            title={`${classItem.subject_name}\n${classItem.classroom}\n${classItem.teacher_name}`}
                            onClick={() => setSelectedGroupId(classItem.conflict_group_id)}
                          >
                            {isConflict && (
                              <div className="conflict-chip">Xung đột {classItem.conflict_size} lớp</div>
                            )}
                            <div className="class-time-row">
                              <span className="class-time">
                                {formatTime(classItem.study_time_start)} - {formatTime(classItem.study_time_end)}
                              </span>
                              <span className="class-room">
                                {classItem.classroom}
                              </span>
                            </div>
                            <div className="class-name">
                              {classItem.subject_id} - {classItem.subject_name}
                            </div>
                            <div className="class-week">
                              Tuần {classItem.study_week}
                            </div>
                          </div>
                        )
                      })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Chi tiết khung giờ đã chọn</h2>
        {!selectedGroup && (
          <div className="text-sm text-gray-600">
            Chọn một ô lớp trên thời khóa biểu để xem đầy đủ các lớp trong cùng khung giờ (bao gồm cả lớp xung đột một phần thời gian).
          </div>
        )}
        {selectedGroup && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
                {daysOfWeekFull[selectedGroup.day_of_week]}
              </span>
              <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
                {formatMinuteToTime(selectedGroup.start_minutes)} - {formatMinuteToTime(selectedGroup.end_minutes)}
              </span>
              <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${selectedGroup.classes.length > 1 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                {selectedGroup.classes.length > 1
                  ? `${selectedGroup.classes.length} lớp xung đột`
                  : 'Không xung đột'}
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {selectedGroup.classes
                .slice()
                .sort((a, b) => a.start_minutes - b.start_minutes)
                .map((cls) => {
                  const subjectColor = getSubjectColor(cls.subject_id)
                  return (
                  <div
                    key={`detail-${cls.id}`}
                    className="rounded-lg border border-gray-200 p-3"
                    style={{
                      borderLeft: `4px solid ${subjectColor.solidColor}`,
                      backgroundColor: subjectColor.softColor
                    }}
                  >
                    <div className="font-semibold text-gray-900">{cls.subject_id} - {cls.subject_name}</div>
                    <div className="text-sm text-gray-600 mt-1">Lớp: {cls.class_name}</div>
                    <div className="text-sm text-gray-600">Giờ học: {formatTime(cls.study_time_start)} - {formatTime(cls.study_time_end)}</div>
                    <div className="text-sm text-gray-600">Phòng: {cls.classroom}</div>
                    <div className="text-sm text-gray-600">Giảng viên: {cls.teacher_name}</div>
                    <div className="text-sm text-gray-600">Tuần: {cls.study_week}</div>
                  </div>
                )})}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Danh sách lớp học</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {classes.map((classItem) => {
            const subjectColor = getSubjectColor(classItem.subject_id)
            return (
            <div
              key={classItem.id}
              className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg"
              style={{
                borderLeft: `4px solid ${subjectColor.solidColor}`,
                backgroundColor: subjectColor.softColor
              }}
            >
              <div className="w-4 h-4 rounded" style={{ backgroundColor: subjectColor.solidColor }}></div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 truncate">
                  {classItem.subject_id} - {classItem.subject_name}
                </div>
                <div className="text-sm text-gray-600">
                  {daysOfWeekFull[classItem.day_of_week]} • {formatTime(classItem.study_time_start)}-{formatTime(classItem.study_time_end)} • {classItem.classroom}
                </div>
                <div className="text-sm text-gray-500">
                  Tuần {classItem.study_week}
                </div>
              </div>
            </div>
          )})}
        </div>

        {classes.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            Không có lịch học nào được tìm thấy
          </div>
        )}
      </div>
    </div>
  )
}

export default Schedule
