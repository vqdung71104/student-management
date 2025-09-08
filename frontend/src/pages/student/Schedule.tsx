import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'

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
  const [selectedDate, setSelectedDate] = useState<number | null>(null)

  const daysOfWeek = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  const daysOfWeekFull = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']

  // Generate calendar dates for current week
  const getCurrentWeekDates = () => {
    const today = new Date()
    const currentDay = today.getDay() // 0 = Sunday, 1 = Monday, etc.
    const startOfWeek = new Date(today)
    startOfWeek.setDate(today.getDate() - currentDay)
    
    const weekDates = []
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek)
      date.setDate(startOfWeek.getDate() + i)
      weekDates.push(date)
    }
    return weekDates
  }

  const weekDates = getCurrentWeekDates()

  useEffect(() => {
    fetchSchedule()
  }, [])

  const fetchSchedule = async () => {
    setLoading(true)
    try {
      if (!userInfo?.student_id) {
        setLoading(false)
        return
      }

      // Bước 1: Lấy thông tin student để có student.id
      const studentResponse = await fetch(`http://localhost:8000/students/${userInfo.student_id}`)
      if (!studentResponse.ok) {
        console.error('Failed to fetch student info')
        setLoading(false)
        return
      }
      const studentData = await studentResponse.json()
      
      // Bước 2: Lấy danh sách class_register theo student.id (integer)
      const classRegisterResponse = await fetch(`http://localhost:8000/class-registers/student-by-id/${studentData.id}`)
      console.log('Class register response status:', classRegisterResponse.status)
      
      if (classRegisterResponse.ok) {
        const classRegisters = await classRegisterResponse.json()
        console.log('Class registers data:', classRegisters)
        
        // Bước 3: Lấy chi tiết từng lớp học theo class_id
        const classDetails = await Promise.all(
          classRegisters.map(async (register: any) => {
            try {
              console.log('Processing class_register:', register)
              
              // Lấy thông tin lớp học theo class_id (đã bao gồm subject info)
              const classResponse = await fetch(`http://localhost:8000/classes/${register.class_id}`)
              if (classResponse.ok) {
                const classData = await classResponse.json()
                console.log('Class data received:', classData)
                
                // Subject data đã có sẵn trong classData.subject
                const subjectData = classData.subject
                
                // Chuyển đổi study_date thành day_of_week
                const dayMap: { [key: string]: number } = {
                  'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                  'Thursday': 4, 'Friday': 5, 'Saturday': 6
                }
                
                const scheduleEntries = []
                
                if (classData.study_date && classData.study_date.includes(',')) {
                  // Nếu có nhiều ngày như "Monday,Friday"
                  const days = classData.study_date.split(',').map((d: string) => d.trim())
                  console.log('Multiple study days:', days)
                  
                  for (const dayName of days) {
                    const dayOfWeek = dayMap[dayName] || 1
                    console.log(`Creating entry for ${dayName} (day ${dayOfWeek})`)
                    
                    scheduleEntries.push({
                      id: register.id,
                      class_name: `${classData.class_name} - ${subjectData.subject_name} - ${subjectData.subject_id}`,
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
                  // Nếu là ngày đơn lẻ
                  let dayOfWeek = 1
                  if (classData.study_date) {
                    if (classData.study_date.includes('-')) {
                      // Date string như "2024-09-08"
                      const studyDate = new Date(classData.study_date)
                      dayOfWeek = studyDate.getDay()
                    } else {
                      // Tên ngày như "Monday"
                      dayOfWeek = dayMap[classData.study_date] || 1
                    }
                  }
                  
                  scheduleEntries.push({
                    id: register.id,
                    class_name: `${classData.class_name} - ${subjectData.subject_name} - ${subjectData.subject_id}`,
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
                
                console.log('Schedule entries created:', scheduleEntries)
                return scheduleEntries
              }
            } catch (error) {
              console.error('Error fetching class details:', error)
            }
            return null
          })
        )
        
        // Flatten array vì mỗi register có thể tạo nhiều entries (multiple days)
        const flattenedClasses = classDetails.flat().filter(item => item !== null)
        console.log('Final flattened classes:', flattenedClasses)
        setClasses(flattenedClasses)
      } else {
        console.error('Failed to fetch class registers')
        setClasses([])
      }
    } catch (error) {
      console.error('Error fetching schedule:', error)
      setClasses([])
    }
    setLoading(false)
  }

  const getClassesForDay = (dayIndex: number) => {
    return classes.filter(cls => cls.day_of_week === dayIndex)
  }

  const hasClassOnDay = (dayIndex: number) => {
    return getClassesForDay(dayIndex).length > 0
  }

  const formatTime = (timeString: string) => {
    if (!timeString) return ''
    // Convert HH:MM:SS to HH:MM
    return timeString.slice(0, 5)
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

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-12 gap-0">
          {/* Calendar Section */}
          <div className="col-span-8 p-6">
            <div className="flex items-center justify-between mb-6">
              <button className="p-2 hover:bg-gray-100 rounded-full">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h2 className="text-xl font-semibold">Tháng 9, 2025</h2>
              <button className="p-2 hover:bg-gray-100 rounded-full">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* Week header */}
            <div className="grid grid-cols-7 mb-4">
              {daysOfWeek.map((day, index) => (
                <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar grid - showing one week */}
            <div className="grid grid-cols-7 gap-1">
              {weekDates.map((date, index) => {
                const dayIndex = date.getDay()
                const hasClass = hasClassOnDay(dayIndex)
                const isSelected = selectedDate === dayIndex
                const isToday = date.toDateString() === new Date().toDateString()
                
                return (
                  <div
                    key={index}
                    className={`relative h-16 border border-gray-200 cursor-pointer hover:bg-gray-50 flex items-center justify-center ${
                      isSelected ? 'bg-blue-50 border-blue-300' : ''
                    } ${isToday ? 'bg-red-50 border-red-300' : ''}`}
                    onClick={() => setSelectedDate(dayIndex)}
                  >
                    <span className={`text-lg ${isToday ? 'text-red-600 font-bold' : 'text-gray-900'}`}>
                      {date.getDate()}
                    </span>
                    {hasClass && (
                      <div className="absolute bottom-1 w-2 h-2 bg-yellow-400 rounded-full"></div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Details Section */}
          <div className="col-span-4 bg-gray-50 p-6 border-l border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Thông tin chi tiết</h3>
            
            {selectedDate !== null ? (
              <div className="space-y-4">
                <h4 className="font-medium text-gray-700">{daysOfWeekFull[selectedDate]}</h4>
                
                {getClassesForDay(selectedDate).map((classItem) => (
                  <div key={classItem.id} className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-start justify-between mb-2">
                      <div className="text-red-600 font-medium text-sm">
                        {formatTime(classItem.study_time_start)}
                      </div>
                      <div className="text-red-600 font-medium text-sm">
                        {classItem.subject_id}
                      </div>
                    </div>
                    
                    <h5 className="font-semibold text-gray-900 mb-3">
                      {`${classItem.class_name} - ${classItem.subject_name} - ${classItem.subject_id}`}
                    </h5>
                    
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex justify-between">
                        <span>Thời gian:</span>
                        <span>{`${formatTime(classItem.study_time_start)} - ${formatTime(classItem.study_time_end)}`}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Địa điểm:</span>
                        <span>{classItem.classroom}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tuần học:</span>
                        <span>{classItem.study_week}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Giảng viên:</span>
                        <span>{classItem.teacher_name}</span>
                      </div>
                    </div>
                  </div>
                ))}
                
                {getClassesForDay(selectedDate).length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    Không có lịch học trong ngày này
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                Chọn một ngày để xem thông tin chi tiết
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Schedule Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Tóm tắt lịch học tuần</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {classes.map((classItem) => (
            <div key={classItem.id} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">
                {`${classItem.class_name} - ${classItem.subject_name}`}
              </h3>
              <div className="space-y-1 text-sm text-gray-600">
                <div>📅 {daysOfWeekFull[classItem.day_of_week]}</div>
                <div>🕐 {formatTime(classItem.study_time_start)} - {formatTime(classItem.study_time_end)}</div>
                <div>📍 {classItem.classroom}</div>
                <div>👨‍🏫 {classItem.teacher_name}</div>
                <div>📚 Tuần {classItem.study_week}</div>
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
