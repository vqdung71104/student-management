import { useState, useRef } from 'react'
import * as XLSX from 'xlsx'

interface ExcelUploadProps {
  onDataParsed: (data: any[]) => void
  onClose: () => void
}

interface ClassData {
  semester: string
  school_department: string
  class_code: string
  class_code_attached: string
  subject_code: string
  subject_name: string
  subject_name_english: string
  credits: string
  note: string
  session_number: string
  day_of_week: string
  time_slot: string
  start_date: string
  end_date: string
  shift: string
  weeks: string
  room: string
  requires_lab: string
  registered_count: string
  max_students: string
  status: string
  class_type: string
  opening_batch: string
  manager_code: string
  system: string
  teaching_type: string
  main_class: string
  session_id: string
  status_id: string
  course_year: string
}

// Utility functions for data conversion
const convertDayOfWeek = (dayNumber: string): string => {
  const dayMap: { [key: string]: string } = {
    '2': 'Monday',
    '3': 'Tuesday', 
    '4': 'Wednesday',
    '5': 'Thursday',
    '6': 'Friday',
    '7': 'Saturday',
    '8': 'Sunday'
  }
  return dayMap[dayNumber] || dayNumber
}

const convertTimeSlot = (timeSlot: string): { startTime: string, endTime: string } => {
  // Convert from "hhmm-hhmm" to "hh:mm" format
  if (!timeSlot || !timeSlot.includes('-')) {
    return { startTime: '', endTime: '' }
  }
  
  const [start, end] = timeSlot.split('-')
  
  const formatTime = (time: string): string => {
    if (time.length === 4) {
      return `${time.substring(0, 2)}:${time.substring(2, 4)}`
    }
    return time
  }
  
  return {
    startTime: formatTime(start.trim()),
    endTime: formatTime(end.trim())
  }
}

const parseStudyWeeks = (weeksString: string): number[] => {
  if (!weeksString) return []
  
  try {
    // Handle different formats like "1-15", "1,2,3", "1-5,8-10", etc.
    const weeks: number[] = []
    const parts = weeksString.split(',')
    
    for (const part of parts) {
      const trimmed = part.trim()
      if (trimmed.includes('-')) {
        const [start, end] = trimmed.split('-').map(x => parseInt(x.trim()))
        if (!isNaN(start) && !isNaN(end)) {
          for (let i = start; i <= end; i++) {
            weeks.push(i)
          }
        }
      } else {
        const week = parseInt(trimmed)
        if (!isNaN(week)) {
          weeks.push(week)
        }
      }
    }
    
    return [...new Set(weeks)].sort((a, b) => a - b) // Remove duplicates and sort
  } catch (error) {
    console.error('Error parsing study weeks:', error)
    return []
  }
}

const ExcelUpload = ({ onDataParsed, onClose }: ExcelUploadProps) => {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<any[]>([])
  const [error, setError] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError('')
      parseExcelFile(selectedFile)
    }
  }

  const parseExcelFile = async (file: File) => {
    setLoading(true)
    try {
      const arrayBuffer = await file.arrayBuffer()
      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      
      // Chuyển đổi sheet thành JSON
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { 
        header: 1,
        defval: ''
      }) as any[][]

      // Tìm dòng header (chứa các trường cần thiết)
      let headerRowIndex = -1
      const requiredFields = ['Kỳ', 'Mã_lớp', 'Mã_HP', 'Tên_HP']
      
      for (let i = 0; i < jsonData.length; i++) {
        const row = jsonData[i]
        if (row && requiredFields.every(field => 
          row.some(cell => cell && cell.toString().includes(field))
        )) {
          headerRowIndex = i
          break
        }
      }

      if (headerRowIndex === -1) {
        throw new Error('Không tìm thấy dòng header với các trường bắt buộc')
      }

      const headers = jsonData[headerRowIndex] as string[]
      const dataRows = jsonData.slice(headerRowIndex + 1)

      // Map headers to our field names
      const fieldMapping = {
        'Kỳ': 'semester',
        'Trường_Viện_Khoa': 'school_department',
        'Mã_lớp': 'class_code',
        'Mã_lớp_kèm': 'class_code_attached',
        'Mã_HP': 'subject_code',
        'Tên_HP': 'subject_name',
        'Tên_HP_Tiếng_Anh': 'subject_name_english',
        'Khối_lượng': 'credits',
        'Ghi_chú': 'note',
        'Buổi_số': 'session_number',
        'Thứ': 'day_of_week',
        'Thời_gian': 'time_slot',
        'BĐ': 'start_date',
        'KT': 'end_date',
        'Kíp': 'shift',
        'Tuần': 'weeks',
        'Phòng': 'room',
        'Cần_TN': 'requires_lab',
        'SLĐK': 'registered_count',
        'SL_Max': 'max_students',
        'Trạng_thái': 'status',
        'Loại_lớp': 'class_type',
        'Đợt_mở': 'opening_batch',
        'Mã_QL': 'manager_code',
        'Hệ': 'system',
        'TeachingType': 'teaching_type',
        'mainclass': 'main_class',
        'Sessionid': 'session_id',
        'Statusid': 'status_id',
        'Khóa': 'course_year'
      }

      // Parse data rows
      const parsedData: any[] = []
      
      for (const row of dataRows) {
        // Skip empty rows
        if (!row || row.every(cell => !cell || cell.toString().trim() === '')) {
          continue
        }

        const classData: any = {}
        
        headers.forEach((header, index) => {
          const fieldName = fieldMapping[header as keyof typeof fieldMapping]
          if (fieldName && row[index]) {
            classData[fieldName] = row[index].toString().trim()
          }
        })

        // Validate required fields
        if (classData.semester && classData.class_code && classData.subject_code && classData.subject_name) {
          // Convert the data to match our API requirements
          const timeSlotData = convertTimeSlot(classData.time_slot)
          const convertedClassData = {
            ...classData,
            day_of_week_converted: convertDayOfWeek(classData.day_of_week),
            study_time_start: timeSlotData.startTime,
            study_time_end: timeSlotData.endTime,
            study_weeks: parseStudyWeeks(classData.weeks)
          }
          parsedData.push(convertedClassData)
        }
      }

      if (parsedData.length === 0) {
        throw new Error('Không tìm thấy dữ liệu hợp lệ trong file')
      }

      setPreview(parsedData.slice(0, 10)) // Show first 10 rows for preview
      
    } catch (error) {
      console.error('Error parsing Excel file:', error)
      setError(error instanceof Error ? error.message : 'Lỗi khi đọc file Excel')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = () => {
    if (file) {
      parseExcelFile(file).then(() => {
        // Parse full data for processing
        const fileReader = new FileReader()
        fileReader.onload = async (e) => {
          try {
            const arrayBuffer = e.target?.result as ArrayBuffer
            const workbook = XLSX.read(arrayBuffer, { type: 'array' })
            const sheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[sheetName]
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' }) as any[][]

            // Find header row and parse all data (same logic as above)
            let headerRowIndex = -1
            const requiredFields = ['Kỳ', 'Mã_lớp', 'Mã_HP', 'Tên_HP']
            
            for (let i = 0; i < jsonData.length; i++) {
              const row = jsonData[i]
              if (row && requiredFields.every(field => 
                row.some(cell => cell && cell.toString().includes(field))
              )) {
                headerRowIndex = i
                break
              }
            }

            const headers = jsonData[headerRowIndex] as string[]
            const dataRows = jsonData.slice(headerRowIndex + 1)

            const fieldMapping = {
              'Kỳ': 'semester',
              'Trường_Viện_Khoa': 'school_department',
              'Mã_lớp': 'class_code',
              'Mã_lớp_kèm': 'class_code_attached',
              'Mã_HP': 'subject_code',
              'Tên_HP': 'subject_name',
              'Tên_HP_Tiếng_Anh': 'subject_name_english',
              'Khối_lượng': 'credits',
              'Ghi_chú': 'note',
              'Buổi_số': 'session_number',
              'Thứ': 'day_of_week',
              'Thời_gian': 'time_slot',
              'BĐ': 'start_date',
              'KT': 'end_date',
              'Kíp': 'shift',
              'Tuần': 'weeks',
              'Phòng': 'room',
              'Cần_TN': 'requires_lab',
              'SLĐK': 'registered_count',
              'SL_Max': 'max_students',
              'Trạng_thái': 'status',
              'Loại_lớp': 'class_type',
              'Đợt_mở': 'opening_batch',
              'Mã_QL': 'manager_code',
              'Hệ': 'system',
              'TeachingType': 'teaching_type',
              'mainclass': 'main_class',
              'Sessionid': 'session_id',
              'Statusid': 'status_id',
              'Khóa': 'course_year'
            }

            const allParsedData: any[] = []
            
            for (const row of dataRows) {
              if (!row || row.every(cell => !cell || cell.toString().trim() === '')) {
                continue
              }

              const classData: any = {}
              
              headers.forEach((header, index) => {
                const fieldName = fieldMapping[header as keyof typeof fieldMapping]
                if (fieldName && row[index]) {
                  classData[fieldName] = row[index].toString().trim()
                }
              })

              if (classData.semester && classData.class_code && classData.subject_code && classData.subject_name) {
                // Convert the data to match our API requirements
                const timeSlotData = convertTimeSlot(classData.time_slot)
                const convertedClassData = {
                  ...classData,
                  day_of_week_converted: convertDayOfWeek(classData.day_of_week),
                  study_time_start: timeSlotData.startTime,
                  study_time_end: timeSlotData.endTime,
                  study_weeks: parseStudyWeeks(classData.weeks)
                }
                allParsedData.push(convertedClassData)
              }
            }

            onDataParsed(allParsedData)
            
          } catch (error) {
            console.error('Error processing file:', error)
            setError('Lỗi khi xử lý file')
          }
        }
        fileReader.readAsArrayBuffer(file)
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
          <h3 className="text-lg font-semibold">📁 Tải lên file Excel thời khóa biểu</h3>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* File Upload Section */}
          <div className="mb-6">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!file ? (
                <div>
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="mt-4">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                    >
                      Chọn file Excel
                    </button>
                    <p className="mt-2 text-sm text-gray-500">
                      Hỗ trợ file .xlsx, .xls
                    </p>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-green-600 mb-2">
                    ✅ File đã chọn: {file.name}
                  </div>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition"
                  >
                    Chọn file khác
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="text-red-800">
                <strong>Lỗi:</strong> {error}
              </div>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Đang xử lý file...</p>
            </div>
          )}

          {/* Preview Data */}
          {preview.length > 0 && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3">📋 Xem trước dữ liệu (10 dòng đầu)</h4>
              <div className="overflow-x-auto max-h-64 border rounded-lg">
                <table className="min-w-full bg-white text-xs">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-2 py-2 text-left">Kỳ</th>
                      <th className="px-2 py-2 text-left">Mã lớp</th>
                      <th className="px-2 py-2 text-left">Mã HP</th>
                      <th className="px-2 py-2 text-left">Tên HP</th>
                      <th className="px-2 py-2 text-left">Thứ</th>
                      <th className="px-2 py-2 text-left">Thời gian</th>
                      <th className="px-2 py-2 text-left">Phòng</th>
                      <th className="px-2 py-2 text-left">SL Max</th>
                      <th className="px-2 py-2 text-left">Loại lớp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, index) => (
                      <tr key={index} className="border-b">
                        <td className="px-2 py-1">{row.semester}</td>
                        <td className="px-2 py-1">{row.class_code}</td>
                        <td className="px-2 py-1">{row.subject_code}</td>
                        <td className="px-2 py-1">{row.subject_name}</td>
                        <td className="px-2 py-1">{row.day_of_week_converted}</td>
                        <td className="px-2 py-1">{row.study_time_start} - {row.study_time_end}</td>
                        <td className="px-2 py-1">{row.room}</td>
                        <td className="px-2 py-1">{row.max_students}</td>
                        <td className="px-2 py-1">{row.class_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Tổng cộng: {preview.length} lớp học được tìm thấy (hiển thị 10 đầu tiên)
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
            >
              Hủy
            </button>
            {preview.length > 0 && (
              <button
                onClick={handleConfirm}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Xác nhận tạo {preview.length} lớp học
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExcelUpload