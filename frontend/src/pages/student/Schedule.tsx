import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import './Schedule.css'

interface ClassSchedule {
  id: number
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

const Schedule = () => {
  const { userInfo } = useAuth()
  const [classes, setClasses] = useState<ClassSchedule[]>([])
  const [loading, setLoading] = useState(true)

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

      const classRegisterResponse = await fetch(`http://localhost:8000/api/class-registers/student/${userInfo.id}`)

      if (classRegisterResponse.ok) {
        const classRegisters = await classRegisterResponse.json()

        const classDetails = await Promise.all(
          classRegisters.map(async (register: any) => {
            try {
              const classResponse = await fetch(`http://localhost:8000/api/classes/${register.class_id}`)
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

  const getClassesForDayAndTime = (dayIndex: number, timeSlot: string) => {
    return classes.filter(cls => {
      if (cls.day_of_week !== dayIndex) return false

      const slotHour = parseInt(timeSlot.split(':')[0])
      const startHour = parseInt(cls.study_time_start.split(':')[0])
      const startMinute = parseInt(cls.study_time_start.split(':')[1])
      const endHour = parseInt(cls.study_time_end.split(':')[0])
      const endMinute = parseInt(cls.study_time_end.split(':')[1])

      // Check if this time slot overlaps with the class time
      const slotStart = slotHour * 60
      const slotEnd = (slotHour + 1) * 60
      const classStart = startHour * 60 + startMinute
      const classEnd = endHour * 60 + endMinute

      return classStart < slotEnd && classEnd > slotStart
    })
  }

  const calculateClassPosition = (classItem: ClassSchedule) => {
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

  // Color palette for different classes
  const getClassColor = (index: number) => {
    const colors = [
      'bg-blue-400',
      'bg-green-400',
      'bg-purple-400',
      'bg-pink-400',
      'bg-yellow-400',
      'bg-indigo-400',
      'bg-red-400',
      'bg-teal-400'
    ]
    return colors[index % colors.length]
  }

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

      {/* Timetable View */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <div className="timetable-container">
            {/* Header with days */}
            <div className="timetable-header">
              <div className="time-column-header"></div>
              {daysOfWeek.map((day, index) => (
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
                    {classes
                      .filter(cls => cls.day_of_week === dayIndex)
                      .map((classItem, idx) => {
                        const position = calculateClassPosition(classItem)
                        const colorClass = getClassColor(idx)

                        return (
                          <div
                            key={classItem.id}
                            className={`class-block ${colorClass}`}
                            style={{
                              top: position.top,
                              height: position.height
                            }}
                            title={`${classItem.subject_name}\n${classItem.classroom}\n${classItem.teacher_name}`}
                          >
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

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Danh sách lớp học</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {classes.map((classItem, idx) => (
            <div key={classItem.id} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg">
              <div className={`w-4 h-4 rounded ${getClassColor(idx)}`}></div>
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
          ))}
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
