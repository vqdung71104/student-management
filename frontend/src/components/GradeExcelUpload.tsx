import { useState, useRef } from 'react'
import * as XLSX from 'xlsx'
import { useAuth } from '../contexts/AuthContext'

interface GradeExcelUploadProps {
  onClose: () => void
  onSuccess: () => void
}

interface ParsedRow {
  semester: string
  subject_code: string
  subject_name: string
  credits: string
  letter_grade: string
}

const GradeExcelUpload = ({ onClose, onSuccess }: GradeExcelUploadProps) => {
  const { userInfo } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<ParsedRow[]>([])
  const [error, setError] = useState<string>('')
  const [progress, setProgress] = useState({ current: 0, total: 0, status: '' })
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
      
      // Convert sheet to JSON without header
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { 
        header: 1,
        defval: ''
      }) as any[][]

      // Parse data rows
      const parsedData: ParsedRow[] = []
      
      for (const row of jsonData) {
        if (!row || row.length < 5 || !row[0] || !row[1]) {
          continue
        }

        const semester = row[0]?.toString().trim()
        const subject_code = row[1]?.toString().trim()
        const subject_name = row[2]?.toString().trim() || ''
        const credits = row[3]?.toString().trim() || ''
        const letter_grade = row[4]?.toString().trim()

        const validGrades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']
        if (semester && subject_code && letter_grade && validGrades.includes(letter_grade)) {
          parsedData.push({
            semester,
            subject_code,
            subject_name,
            credits,
            letter_grade
          })
        }
      }

      if (parsedData.length === 0) {
        throw new Error('No valid grade data found')
      }

      setPreview(parsedData)
      
    } catch (error) {
      console.error('Error parsing Excel:', error)
      setError(error instanceof Error ? error.message : 'Error reading Excel file')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview.length || !userInfo?.id) {
      setError('Missing student info or data')
      return
    }

    setLoading(true)
    setProgress({ current: 0, total: preview.length, status: 'Adding grades...' })

    let successCount = 0
    let errorCount = 0
    const errors: string[] = []

    for (let i = 0; i < preview.length; i++) {
      const row = preview[i]
      setProgress({ 
        current: i + 1, 
        total: preview.length, 
        status: `Processing ${i + 1}/${preview.length}: ${row.subject_code}...` 
      })

      try {
        const response = await fetch('http://localhost:8000/api/learned-subjects/create-new-learned-subject', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            student_id: userInfo.id,
            subject_id: row.subject_code,
            semester: row.semester,
            letter_grade: row.letter_grade
          })
        })

        if (response.ok) {
          successCount++
        } else {
          const error = await response.json()
          errorCount++
          errors.push(`${row.subject_code}: ${error.detail || 'Unknown error'}`)
        }
      } catch (error) {
        errorCount++
        errors.push(`${row.subject_code}: ${error instanceof Error ? error.message : 'Connection error'}`)
      }

      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const resultMessage = `Complete!\n\nSuccess: ${successCount}\nErrors: ${errorCount}` +
      (errors.length > 0 ? `\n\nFirst errors:\n${errors.slice(0, 5).join('\n')}` : '')
    
    alert(resultMessage)
    
    if (successCount > 0) {
      onSuccess()
    }
    
    onClose()
    setLoading(false)
    setProgress({ current: 0, total: 0, status: '' })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="bg-blue-600 text-white p-4 flex justify-between items-center sticky top-0">
          <h3 className="text-lg font-semibold">Upload Grades from Excel</h3>
          <button onClick={onClose} className="text-white hover:text-gray-200" disabled={loading}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Hướng dẫn:</h4>
            <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
              <li>Truy cập https://ctt.hust.edu.vn/ và đăng nhập</li>
              <li>Chọn: Dịch vụ  Kết quả học tập  Điểm cá nhân</li>
              <li>Sao chép toàn bộ bảng điểm và dán vào trang tính Excel trống</li>
              <li>Lưu tệp Excel và tải lên đây</li>
            </ol>
            <div className="mt-3 text-xs text-blue-700 bg-white p-2 rounded">
              <strong>Định dạng file:</strong> Dữ liệu bắt đầu từ cột A (không cần tiêu đề)<br />
              <strong>Thứ tự cột:</strong> A=Học kỳ, B=Mã HP, C=Tên HP, D=Số tín chỉ, E=Điểm chữ
            </div>
          </div>

          <div className="mb-6">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
                disabled={loading}
              />
              
              {!file ? (
                <div>
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="mt-4">
                    <button onClick={() => fileInputRef.current?.click()} className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition" disabled={loading}>
                      Chọn tệp
                    </button>
                    <p className="mt-2 text-sm text-gray-500">Hỗ trợ các tệp .xlsx, .xls</p>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-green-600 mb-2">File đã chọn: {file.name}</div>
                  <button onClick={() => fileInputRef.current?.click()} className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition" disabled={loading}>
                    Chọn tệp khác
                  </button>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="text-red-800"><strong>Error:</strong> {error}</div>
            </div>
          )}

          {loading && progress.total > 0 && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="mb-2 flex justify-between text-sm">
                <span className="font-semibold text-blue-900">{progress.status}</span>
                <span className="text-blue-700">{progress.current}/{progress.total}</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-4 overflow-hidden">
                <div className="bg-blue-600 h-4 rounded-full transition-all duration-300" style={{ width: `${(progress.current / progress.total) * 100}%` }}></div>
              </div>
            </div>
          )}

          {loading && progress.total === 0 && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Đang xử lý tệp...</p>
            </div>
          )}

          {preview.length > 0 && !loading && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3">Preview ({preview.length > 10 ? 'First 10 rows' : `${preview.length} rows`})</h4>
              <div className="overflow-x-auto max-h-64 border rounded-lg">
                <table className="min-w-full bg-white text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">Học kỳ</th>
                      <th className="px-4 py-2 text-left">Mã học phần</th>
                      <th className="px-4 py-2 text-left">Tên học phần</th>
                      <th className="px-4 py-2 text-left">Số tín chỉ</th>
                      <th className="px-4 py-2 text-left">Điểm chữ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.slice(0, 10).map((row, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-2">{row.semester}</td>
                        <td className="px-4 py-2 font-mono">{row.subject_code}</td>
                        <td className="px-4 py-2">{row.subject_name}</td>
                        <td className="px-4 py-2 text-center">{row.credits}</td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                            row.letter_grade === 'F' ? 'bg-red-100 text-red-800' :
                            ['A+', 'A'].includes(row.letter_grade) ? 'bg-green-100 text-green-800' :
                            ['B+', 'B'].includes(row.letter_grade) ? 'bg-blue-100 text-blue-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {row.letter_grade}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-gray-600 mt-2">Tổng cộng: {preview.length} môn học</p>
            </div>
          )}

          <div className="flex justify-end space-x-4">
            <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition" disabled={loading}>
              {loading ? 'Processing...' : 'Cancel'}
            </button>
            {preview.length > 0 && (
              <button onClick={handleConfirm} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed" disabled={loading}>
                {loading ? 'Adding...' : `Confirm Add ${preview.length} Subjects`}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GradeExcelUpload
