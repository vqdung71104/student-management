import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'

interface ScheduleItem {
  id: number
  subject_code: string
  subject_name: string
  class_id: string
  teacher: string
  room: string
  day_of_week: number
  start_time: string
  end_time: string
  weeks: string
}

const Schedule = () => {
  const { userInfo } = useAuth()
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [loading, setLoading] = useState(true)

  const daysOfWeek = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
  const timeSlots = [
    '7:00-8:50', '9:00-10:50', '13:00-14:50', '15:00-16:50', '17:00-18:50', '19:00-20:50'
  ]

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

      // Lấy danh sách lớp đăng ký của sinh viên
      const response = await fetch(`http://localhost:8000/class-registers/student/${userInfo.student_id}`)
      if (response.ok) {
        const classRegisters = await response.json()
        
        // Chuyển đổi thành định dạng schedule
        const scheduleData = await Promise.all(
          classRegisters.map(async (register: any) => {
            try {
              // Lấy thông tin chi tiết lớp học
              const classResponse = await fetch(`http://localhost:8000/classes/${register.class_id}`)
              if (classResponse.ok) {
                const classData = await classResponse.json()
                
                // Lấy thông tin môn học
                const subjectResponse = await fetch(`http://localhost:8000/subjects/${classData.subject_id}`)
                if (subjectResponse.ok) {
                  const subjectData = await subjectResponse.json()
                  
                  return {
                    id: register.id,
                    subject_code: subjectData.subject_id,
                    subject_name: subjectData.subject_name,
                    class_id: classData.class_id,
                    teacher: classData.teacher_name || 'Chưa phân công',
                    room: classData.room || 'Chưa phân phòng',
                    day_of_week: classData.day_of_week || 2,
                    start_time: classData.start_time || '07:00',
                    end_time: classData.end_time || '08:50',
                    weeks: classData.weeks || '1-16'
                  }
                }
              }
            } catch (error) {
              console.error('Error fetching class details:', error)
            }
            return null
          })
        )
        
        setSchedule(scheduleData.filter(item => item !== null))
      } else {
        console.error('Failed to fetch class registers')
        setSchedule([])
      }
    } catch (error) {
      console.error('Error fetching schedule:', error)
      setSchedule([])
    }
    setLoading(false)
  }

  const getScheduleForDay = (dayIndex: number) => {
    return schedule.filter(item => item.day_of_week === dayIndex)
  }

  const getScheduleForTimeSlot = (dayIndex: number, timeSlot: string) => {
    const daySchedule = getScheduleForDay(dayIndex)
    return daySchedule.find(item => {
      const itemTime = `${item.start_time}-${item.end_time}`
      return itemTime === timeSlot.replace(':', '')
    })
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
        <div className="text-sm text-gray-600">
          Học kỳ 2023-2024.1 | Sinh viên: {userInfo?.student_name}
        </div>
      </div>

      {/* Schedule Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-blue-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border border-gray-200">
                  Tiết
                </th>
                {daysOfWeek.slice(1, 7).map((day, index) => (
                  <th key={index} className="px-4 py-3 text-center text-sm font-semibold text-gray-900 border border-gray-200 min-w-32">
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeSlots.map((timeSlot, slotIndex) => (
                <tr key={slotIndex} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm font-medium text-gray-900 border border-gray-200 bg-gray-50">
                    <div className="text-center">
                      <div className="font-semibold">Tiết {slotIndex * 2 + 1}-{slotIndex * 2 + 2}</div>
                      <div className="text-xs text-gray-600">{timeSlot}</div>
                    </div>
                  </td>
                  {[2, 3, 4, 5, 6, 7].map((dayIndex) => {
                    const scheduleItem = getScheduleForTimeSlot(dayIndex, timeSlot)
                    return (
                      <td key={dayIndex} className="px-2 py-4 border border-gray-200 align-top">
                        {scheduleItem ? (
                          <div className="bg-blue-100 border border-blue-300 rounded-lg p-2 text-xs">
                            <div className="font-semibold text-blue-900 mb-1">
                              {scheduleItem.subject_code}
                            </div>
                            <div className="text-blue-800 mb-1">
                              {scheduleItem.subject_name}
                            </div>
                            <div className="text-blue-700 mb-1">
                              Lớp: {scheduleItem.class_id}
                            </div>
                            <div className="text-blue-700 mb-1">
                              GV: {scheduleItem.teacher}
                            </div>
                            <div className="text-blue-600">
                              📍 {scheduleItem.room}
                            </div>
                            <div className="text-blue-600 mt-1">
                              Tuần: {scheduleItem.weeks}
                            </div>
                          </div>
                        ) : (
                          <div className="h-24"></div>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Schedule Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Tóm tắt môn học</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from(new Set(schedule.map(item => item.subject_code))).map(subjectCode => {
            const subjectItems = schedule.filter(item => item.subject_code === subjectCode)
            const mainSubject = subjectItems[0]
            return (
              <div key={subjectCode} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900">{mainSubject.subject_name}</h3>
                <p className="text-sm text-gray-600 mb-2">Mã môn: {subjectCode}</p>
                <p className="text-sm text-gray-600 mb-2">GV: {mainSubject.teacher}</p>
                <div className="space-y-1">
                  {subjectItems.map(item => (
                    <div key={item.id} className="text-xs text-gray-500">
                      {daysOfWeek[item.day_of_week]} {item.start_time}-{item.end_time} tại {item.room}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default Schedule
