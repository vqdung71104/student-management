import { useState, useEffect, useRef } from 'react'
import ExcelUpload from '../../components/ExcelUpload'
import * as XLSX from 'xlsx'

// Teacher Update Modal Component
const TeacherUpdateModal = ({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) => {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const processExcelFile = async (file: File): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer)
          const workbook = XLSX.read(data, { type: 'array' })
          const worksheet = workbook.Sheets[workbook.SheetNames[0]]
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
          
          // Tìm dòng header có chứa các cột cần thiết
          let headerRowIndex = -1
          for (let i = 0; i < jsonData.length; i++) {
            const row = jsonData[i] as any[]
            if (row.some(cell => 
              cell && (
                String(cell).toLowerCase().includes('mã_lớp') || 
                String(cell).toLowerCase().includes('mã lớp') ||
                String(cell).toLowerCase().includes('giảng viên')
              )
            )) {
              headerRowIndex = i
              break
            }
          }

          if (headerRowIndex === -1) {
            throw new Error('Không tìm thấy header có các cột: Mã_lớp, Mã_lớp_kèm, Giảng viên giảng dạy')
          }

          const headers = jsonData[headerRowIndex] as any[]
          const teacherUpdates: any[] = []

          // Tìm index của các cột cần thiết
          const classIdIndex = headers.findIndex((h: any) => 
            h && (String(h).includes('Mã_lớp') && !String(h).includes('kèm'))
          )
          const classIdKemIndex = headers.findIndex((h: any) => 
            h && String(h).includes('Mã_lớp_kèm')
          )
          const teacherIndex = headers.findIndex((h: any) => 
            h && String(h).includes('Giảng viên giảng dạy')
          )

          if (classIdIndex === -1 || classIdKemIndex === -1 || teacherIndex === -1) {
            throw new Error('Không tìm thấy đầy đủ các cột: Mã_lớp, Mã_lớp_kèm, Giảng viên giảng dạy')
          }

          // Xử lý dữ liệu từ dòng sau header
          for (let i = headerRowIndex + 1; i < jsonData.length; i++) {
            const row = jsonData[i] as any[]
            if (row.length > Math.max(classIdIndex, classIdKemIndex, teacherIndex)) {
              const classId = row[classIdIndex]
              const classIdKem = row[classIdKemIndex]
              const teacher = row[teacherIndex]

              // Chỉ xử lý nếu tất cả 3 giá trị đều có
              if (classId && classIdKem && teacher) {
                teacherUpdates.push({
                  class_id: String(classId).trim(),
                  class_id_kem: String(classIdKem).trim(),
                  teacher: String(teacher).trim()
                })
              }
            }
          }

          if (teacherUpdates.length === 0) {
            throw new Error('Không tìm thấy dữ liệu hợp lệ trong file')
          }

          resolve(teacherUpdates)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = () => reject(new Error('Lỗi khi đọc file'))
      reader.readAsArrayBuffer(file)
    })
  }

  const handleSubmit = async () => {
    if (!file) {
      alert('Vui lòng chọn file Excel')
      return
    }

    setLoading(true)
    try {
      // Xử lý file Excel
      const teacherUpdates = await processExcelFile(file)
      
      // Gửi dữ liệu đến API
      const response = await fetch('/api/classes/update-teachers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ updates: teacherUpdates }),
      })

      if (response.ok) {
        const result = await response.json()
        alert(`Cập nhật thành công! ${result.updated_count} lớp đã được cập nhật giáo viên.`)
        onSuccess()
      } else {
        const error = await response.text()
        throw new Error(error)
      }
    } catch (error) {
      console.error('Error updating teachers:', error)
      alert(`Lỗi: ${error instanceof Error ? error.message : 'Có lỗi xảy ra'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Cập nhật giáo viên</h2>
        
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div>
              <p className="text-green-600 font-medium">{file.name}</p>
              <p className="text-sm text-gray-500 mt-1">Kích thước: {(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div>
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-gray-600">Kéo thả file Excel vào đây hoặc</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:underline mt-2"
              >
                chọn file từ máy tính
              </button>
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
        />

        <div className="mt-4 text-sm text-gray-600">
          <p><strong>Lưu ý:</strong> File Excel cần có các cột:</p>
          <ul className="list-disc list-inside mt-1">
            <li>Mã_lớp</li>
            <li>Mã_lớp_kèm</li>
            <li>Giảng viên giảng dạy</li>
          </ul>
        </div>

        <div className="flex justify-end space-x-4 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
            disabled={loading}
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !file}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
          >
            {loading ? 'Đang xử lý...' : 'Cập nhật'}
          </button>
        </div>
      </div>
    </div>
  )
}

const ScheduleManagement = () => {
  const [classes, setClasses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showExcelUpload, setShowExcelUpload] = useState(false)
  const [showTeacherUpdate, setShowTeacherUpdate] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingClass, setEditingClass] = useState<any>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [schedPage, setSchedPage] = useState(1)
  const [schedPageSize, setSchedPageSize] = useState(10)
  
  // Refs for scroll synchronization
  const topScrollRef = useRef<HTMLDivElement>(null)
  const mainScrollRef = useRef<HTMLDivElement>(null)
  const bottomScrollRef = useRef<HTMLDivElement>(null)

  const getAuthRequestOptions = (options: RequestInit = {}): RequestInit => {
    const token = localStorage.getItem('access_token')
    return {
      ...options,
      credentials: 'include',
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  }

  useEffect(() => {
    fetchClasses()
  }, [])

  // Reset to first page whenever search term changes
  useEffect(() => {
    setSchedPage(1)
  }, [searchTerm])

  // Synchronize scroll bars
  const handleScroll = (source: 'top' | 'main' | 'bottom') => (e: React.UIEvent<HTMLDivElement>) => {
    const scrollLeft = e.currentTarget.scrollLeft
    
    if (source !== 'top' && topScrollRef.current) {
      topScrollRef.current.scrollLeft = scrollLeft
    }
    if (source !== 'main' && mainScrollRef.current) {
      mainScrollRef.current.scrollLeft = scrollLeft
    }
    if (source !== 'bottom' && bottomScrollRef.current) {
      bottomScrollRef.current.scrollLeft = scrollLeft
    }
  }

  const fetchClasses = async () => {
    try {
      const response = await fetch('/api/classes/', getAuthRequestOptions())
      if (response.ok) {
        const data = await response.json()
        // Fetch current student count for each class
        const classesWithStudentCount = await Promise.all(
          data.map(async (classItem: any) => {
            try {
              const registersResponse = await fetch(
                `/api/class-registers/class/${classItem.id}`,
                getAuthRequestOptions()
              )
              if (registersResponse.ok) {
                const registers = await registersResponse.json()
                return {
                  ...classItem,
                  current_students: registers.length
                }
              }
            } catch (error) {
              console.error(`Error fetching student count for class ${classItem.id}:`, error)
            }
            return {
              ...classItem,
              current_students: 0
            }
          })
        )
        setClasses(classesWithStudentCount)
      }
    } catch (error) {
      console.error('Error fetching classes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteClass = async (classId: number) => {
    if (window.confirm('Bạn có chắc chắn muốn xóa lớp học này?')) {
      try {
        const response = await fetch(`/api/classes/${classId}`, {
          method: 'DELETE'
        })
        
        if (response.ok) {
          alert('Xóa lớp học thành công!')
          fetchClasses() // Refresh the list
        } else {
          alert('Có lỗi khi xóa lớp học')
        }
      } catch (error) {
        console.error('Error deleting class:', error)
        alert('Có lỗi khi xóa lớp học')
      }
    }
  }

  const handleEditClass = (classItem: any) => {
    setEditingClass(classItem)
    setShowEditModal(true)
  }

  const handleUpdateClass = async (updatedClass: any) => {
    try {
      const response = await fetch(`/api/classes/${updatedClass.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          class_id: updatedClass.class_id,
          class_name: updatedClass.class_name,
          linked_class_ids: updatedClass.linked_class_ids || [],
          class_type: updatedClass.class_type,
          classroom: updatedClass.classroom,
          study_date: updatedClass.study_date,
          study_time_start: updatedClass.study_time_start,
          study_time_end: updatedClass.study_time_end,
          teacher_name: updatedClass.teacher_name,
          study_week: updatedClass.study_week || []
        }),
      })

      if (response.ok) {
        const updatedClassFromAPI = await response.json()
        
        // Update the class in the current state immediately
        setClasses(prevClasses => 
          prevClasses.map(classItem => 
            classItem.id === updatedClassFromAPI.id 
              ? { ...updatedClassFromAPI, current_students: classItem.current_students } 
              : classItem
          )
        )
        
        alert('Cập nhật lớp học thành công!')
        setShowEditModal(false)
        setEditingClass(null)
      } else {
        alert('Có lỗi khi cập nhật lớp học')
      }
    } catch (error) {
      console.error('Error updating class:', error)
      alert('Có lỗi khi cập nhật lớp học')
    }
  }

  // Filter classes based on search term
  const filteredClasses = classes.filter((classItem: any) =>
    classItem.class_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.class_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.classroom?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.teacher_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classItem.class_type?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const schedTotalPages = Math.max(1, Math.ceil(filteredClasses.length / schedPageSize))
  const paginatedClasses = filteredClasses.slice((schedPage - 1) * schedPageSize, schedPage * schedPageSize)

  const handleExcelDataParsed = async (excelData: any[]) => {
    setCreateLoading(true)
    setShowExcelUpload(false)
    
    try {
      const successCount = await createClassesFromExcel(excelData)
      
      // Refresh the list
      await fetchClasses()
      
      // Show success message only if all succeeded
      if (successCount === excelData.length) {
        alert(`✅ Tạo thành công tất cả ${successCount} lớp học!`)
      }
      // Error details are already shown in createClassesFromExcel function
    } catch (error) {
      console.error('Error creating classes:', error)
      alert('❌ Có lỗi xảy ra khi tạo lớp học. Vui lòng kiểm tra console (F12) để biết chi tiết.')
    } finally {
      setCreateLoading(false)
    }
  }

  const createSubjectIfNotExists = async (subjectCode: string, subjectName: string): Promise<number> => {
    try {
      // Create a new subject
      const subjectData = {
        subject_id: subjectCode,
        subject_name: subjectName,
        duration: 15, // Default values
        credits: 3,
        tuition_fee: 1000000,
        english_subject_name: subjectName,
        weight: 1.0,
        department_id: "string" // Use first department ID
      }

      const response = await fetch('/api/subjects/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subjectData),
      })

      if (response.ok) {
        const newSubject = await response.json()
        console.log(`Created new subject: ${subjectCode}`)
        return newSubject.id
      } else {
        console.error(`Failed to create subject ${subjectCode}:`, await response.text())
        return 1 // Fallback to default
      }
    } catch (error) {
      console.error(`Error creating subject ${subjectCode}:`, error)
      return 1 // Fallback to default
    }
  }

  const createClassesFromExcel = async (excelData: any[]): Promise<number> => {
    let successCount = 0
    const errors: { class_code: string, reason: string }[] = []
    
    // First, get all subjects to map subject_code to subject_id
    let subjectsMap: { [key: string]: number } = {}
    try {
      const subjectsResponse = await fetch('/api/subjects/')
      if (subjectsResponse.ok) {
        const subjects = await subjectsResponse.json()
        subjectsMap = subjects.reduce((map: any, subject: any) => {
          map[subject.subject_id] = subject.id
          return map
        }, {})
      }
    } catch (error) {
      console.error('Error fetching subjects:', error)
    }
    
    // Check for existing classes to avoid duplicates
    let existingClassIds: Set<string> = new Set()
    try {
      const classesResponse = await fetch('/api/classes/')
      if (classesResponse.ok) {
        const existingClasses = await classesResponse.json()
        existingClassIds = new Set(existingClasses.map((c: any) => c.class_id))
      }
    } catch (error) {
      console.error('Error fetching existing classes:', error)
    }
    
    console.log(` Starting bulk upload: ${excelData.length} classes`)
    console.log(` Found ${existingClassIds.size} existing classes in database`)
    
    for (let i = 0; i < excelData.length; i++) {
      const row = excelData[i]
      const classCode = row.class_code || `Row_${i + 1}`
      
      try {
        // Validation 1: Check duplicate class_id
        if (existingClassIds.has(row.class_code)) {
          errors.push({ class_code: classCode, reason: '❌ Duplicate: Class ID already exists' })
          console.warn(`⚠️ Skipping ${classCode}: Already exists in database`)
          continue
        }
        
        // Validation 2: Check required fields
        if (!row.class_code || !row.subject_name || !row.subject_code) {
          errors.push({ class_code: classCode, reason: '❌ Missing required fields (class_code, subject_name, subject_code)' })
          console.warn(`⚠️ Skipping ${classCode}: Missing required fields`)
          continue
        }
        
        // Map subject_code to subject_id, create new subject if not found
        let subjectId = subjectsMap[row.subject_code]
        if (!subjectId) {
          console.warn(`⚠️ Subject not found for code: ${row.subject_code}, creating new subject...`)
          subjectId = await createSubjectIfNotExists(row.subject_code, row.subject_name)
          subjectsMap[row.subject_code] = subjectId // Cache for future use
        }

        // Map Excel fields to API fields according to ClassCreate schema
        const classData = {
          // Required fields mapped from Excel
          class_id: row.class_code,
          class_name: row.subject_name,
          subject_id: subjectId,
          
          // Optional fields mapped from Excel
          linked_class_ids: row.class_code_attached ? [row.class_code_attached] : [],
          class_type: row.class_type || '',
          classroom: row.room || '',
          study_date: row.day_of_week_converted || '',
          study_time_start: row.study_time_start || '',
          study_time_end: row.study_time_end || '',
          teacher_name: row.teacher_name || '',
          study_week: row.study_weeks || []
        }

        console.log(`📤 [${i + 1}/${excelData.length}] Creating class: ${classCode}`)

        const response = await fetch('/api/classes/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(classData),
        })

        if (response.ok) {
          successCount++
          existingClassIds.add(row.class_code) // Add to set to prevent duplicates in same batch
          console.log(`✅ [${i + 1}/${excelData.length}] Success: ${classCode}`)
        } else {
          const errorText = await response.text()
          let errorReason = '❌ Server error'
          
          try {
            const errorJson = JSON.parse(errorText)
            errorReason = `❌ ${errorJson.detail || errorText}`
          } catch {
            errorReason = `❌ ${errorText.substring(0, 100)}`
          }
          
          errors.push({ class_code: classCode, reason: errorReason })
          console.error(`❌ [${i + 1}/${excelData.length}] Failed: ${classCode} - ${errorReason}`)
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error)
        errors.push({ class_code: classCode, reason: `❌ Exception: ${errorMsg}` })
        console.error(`❌ [${i + 1}/${excelData.length}] Exception: ${classCode}`, error)
      }
    }
    
    // Display detailed summary
    console.log(`\n📊 Upload Summary:`)
    console.log(`✅ Success: ${successCount}/${excelData.length}`)
    console.log(`❌ Failed: ${errors.length}/${excelData.length}`)
    
    if (errors.length > 0) {
      console.log(`\n❌ Failed Classes:`)
      errors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err.class_code}: ${err.reason}`)
      })
      
      // Show alert with error details
      const errorSummary = errors.slice(0, 10).map(e => `• ${e.class_code}: ${e.reason}`).join('\n')
      const remainingErrors = errors.length > 10 ? `\n... và ${errors.length - 10} lỗi khác` : ''
      alert(`⚠️ Hoàn thành với lỗi!\n\n✅ Tạo thành công: ${successCount}/${excelData.length}\n❌ Thất bại: ${errors.length}\n\nChi tiết lỗi:\n${errorSummary}${remainingErrors}\n\nXem console (F12) để biết chi tiết đầy đủ.`)
    }
    
    return successCount
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">   Quản lý thời khóa biểu</h1>
          <p className="text-gray-600">Quản lý lịch học và thời khóa biểu của các lớp</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setShowExcelUpload(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center space-x-2"
            disabled={createLoading}
          >
            {createLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Đang tạo...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>Tải file Excel</span>
              </>
            )}
          </button>
          
          <button
            onClick={() => setShowTeacherUpdate(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Cập nhật giáo viên</span>
          </button>
          
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
               Thêm lớp thủ công
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Tổng số lớp</p>
              <p className="text-2xl font-semibold text-gray-900">{classes.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Lớp đang hoạt động</p>
              <p className="text-2xl font-semibold text-gray-900">
                {classes.filter((c: any) => c.status === 'active').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Học kỳ hiện tại</p>
              <p className="text-2xl font-semibold text-gray-900">2024.1</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Phòng học</p>
              <p className="text-2xl font-semibold text-gray-900">
                {new Set(classes.map((c: any) => c.room)).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <input
          type="text"
          placeholder="Tìm kiếm theo mã lớp, tên lớp, phòng học, giảng viên, loại lớp..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Classes Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Danh sách lớp học ({filteredClasses.length} lớp)
          </h3>
        </div>
        
        {/* Top Scroll Bar */}
        <div 
          ref={topScrollRef}
          className="overflow-x-auto border-b border-gray-100" 
          style={{ overflowX: 'scroll' }}
          onScroll={handleScroll('top')}
        >
          <div style={{ minWidth: '2200px', height: '20px' }}>
            <div className="w-full h-px bg-gray-200"></div>
          </div>
        </div>
        
        {/* Main Table Container */}
        <div 
          ref={mainScrollRef}
          className="overflow-x-auto overflow-y-auto" 
          style={{ overflowX: 'scroll', maxHeight: '60vh' }}
          onScroll={handleScroll('main')}
        >
          <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '1200px' }}>
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Mã lớp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Tên lớp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Loại lớp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Thời gian
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Phòng
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Giảng viên
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Sĩ số
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedClasses.map((classItem: any) => (
                <tr key={classItem.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {classItem.class_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {classItem.class_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {classItem.class_type || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {classItem.study_date} - {classItem.study_time_start}~{classItem.study_time_end} 
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {classItem.classroom}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {classItem.teacher_name || 'Chưa phân công'}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button 
                      onClick={() => handleEditClass(classItem)}
                      className="text-indigo-600 hover:text-indigo-900 mr-2 transition-colors"
                    >
                         Sửa
                    </button>
                    <button 
                      onClick={() => handleDeleteClass(classItem.id)}
                      className="text-red-600 hover:text-red-900 transition-colors"
                    >
                        Xóa
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Bottom Scroll Bar */}
        <div 
          ref={bottomScrollRef}
          className="overflow-x-auto border-t border-gray-100" 
          style={{ overflowX: 'scroll' }}
          onScroll={handleScroll('bottom')}
        >
          <div style={{ minWidth: '1200px', height: '20px' }}>
            <div className="w-full h-px bg-gray-200"></div>
          </div>
        </div>

        {filteredClasses.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">
              {searchTerm ? 'Không tìm thấy lớp học nào phù hợp' : 'Chưa có lớp học nào'}
            </p>
          </div>
        )}

        {/* Pagination */}
        {filteredClasses.length > 0 && (
          <div className="px-6 py-3 border-t border-gray-200 flex flex-wrap items-center justify-between gap-3 bg-white">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>Hiển thị</span>
              <select
                className="border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                value={schedPageSize}
                onChange={(e) => { setSchedPageSize(Number(e.target.value)); setSchedPage(1) }}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
              <span>dòng / trang &nbsp;•&nbsp; Tổng {filteredClasses.length} lớp</span>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <button
                disabled={schedPage === 1}
                onClick={() => setSchedPage(1)}
                className="h-8 px-2 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >&laquo;</button>
              <button
                disabled={schedPage === 1}
                onClick={() => setSchedPage(p => p - 1)}
                className="h-8 px-2 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >&lsaquo;</button>
              {Array.from({ length: schedTotalPages }, (_, i) => i + 1)
                .filter(p => p === 1 || p === schedTotalPages || Math.abs(p - schedPage) <= 2)
                .reduce<(number | 'ellipsis1' | 'ellipsis2')[]>((acc, p, idx, src) => {
                  if (idx > 0 && p - (src[idx - 1] as number) > 1) {
                    acc.push(acc.length === 1 ? 'ellipsis1' : 'ellipsis2')
                  }
                  acc.push(p)
                  return acc
                }, [])
                .map((item) =>
                  item === 'ellipsis1' || item === 'ellipsis2'
                    ? <span key={item} className="h-8 px-1 flex items-center text-gray-400">…</span>
                    : <button
                        key={item}
                        onClick={() => setSchedPage(item as number)}
                        className={`h-8 w-8 rounded border text-sm transition-colors ${
                          schedPage === item
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'border-gray-300 text-gray-600 hover:bg-gray-100'
                        }`}
                      >{item}</button>
                )
              }
              <button
                disabled={schedPage === schedTotalPages}
                onClick={() => setSchedPage(p => p + 1)}
                className="h-8 px-2 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >&rsaquo;</button>
              <button
                disabled={schedPage === schedTotalPages}
                onClick={() => setSchedPage(schedTotalPages)}
                className="h-8 px-2 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >&raquo;</button>
            </div>
          </div>
        )}
      </div>

      {/* Excel Upload Modal */}
      {showExcelUpload && (
        <ExcelUpload
          onDataParsed={handleExcelDataParsed}
          onClose={() => setShowExcelUpload(false)}
        />
      )}

      {/* Edit Class Modal */}
      {showEditModal && editingClass && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Sửa thông tin lớp học</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mã lớp</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.class_id || ''}
                  onChange={(e) => setEditingClass({...editingClass, class_id: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tên lớp</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.class_name || ''}
                  onChange={(e) => setEditingClass({...editingClass, class_name: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loại lớp</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.class_type || ''}
                  onChange={(e) => setEditingClass({...editingClass, class_type: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phòng học</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.classroom || ''}
                  onChange={(e) => setEditingClass({...editingClass, classroom: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Thứ</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.study_date || ''}
                  onChange={(e) => setEditingClass({...editingClass, study_date: e.target.value})}
                >
                  <option value="">Chọn thứ</option>
                  <option value="Monday">Thứ 2</option>
                  <option value="Tuesday">Thứ 3</option>
                  <option value="Wednesday">Thứ 4</option>
                  <option value="Thursday">Thứ 5</option>
                  <option value="Friday">Thứ 6</option>
                  <option value="Saturday">Thứ 7</option>
                  <option value="Sunday">Chủ nhật</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Giờ bắt đầu</label>
                  <input
                    type="time"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    value={editingClass.study_time_start || ''}
                    onChange={(e) => setEditingClass({...editingClass, study_time_start: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Giờ kết thúc</label>
                  <input
                    type="time"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    value={editingClass.study_time_end || ''}
                    onChange={(e) => setEditingClass({...editingClass, study_time_end: e.target.value})}
                  />
                </div>
              </div>

              

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Giảng viên</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={editingClass.teacher_name || ''}
                  onChange={(e) => setEditingClass({...editingClass, teacher_name: e.target.value})}
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingClass(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                Hủy
              </button>
              <button
                onClick={() => handleUpdateClass(editingClass)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Teacher Update Modal */}
      {showTeacherUpdate && (
        <TeacherUpdateModal 
          onClose={() => setShowTeacherUpdate(false)}
          onSuccess={() => {
            setShowTeacherUpdate(false)
            fetchClasses() // Refresh classes after update
          }}
        />
      )}
    </div>
  )
}

export default ScheduleManagement