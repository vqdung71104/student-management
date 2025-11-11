import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Table, Modal, message, Space, Tag, Typography, Card, Input, Select } from 'antd'
import { SearchOutlined, BookOutlined, PlusOutlined, ArrowLeftOutlined, CalendarOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography
const { Option } = Select

interface Subject {
  id: number
  subject_name: string
  subject_id: string
  credits: number
  semester: number
  subject_type: string
  duration: number
  description?: string
}

interface SubjectRegister {
  id: number
  student_id: number
  subject_id: number
  subject_name: string
  credits: number
  register_date: string
}

const SubjectRegistration = () => {
  const { userInfo } = useAuth()
  const navigate = useNavigate()
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [registeredSubjects, setRegisteredSubjects] = useState<SubjectRegister[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [searchText, setSearchText] = useState('')
  const [filterSemester, setFilterSemester] = useState<number | null>(null)
  const [filterType, setFilterType] = useState<string | null>(null)
  const [studentData, setStudentData] = useState<any>(null)

  // Fetch student data first
  const fetchStudentData = async () => {
    if (!userInfo?.id) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/students/${userInfo.id}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Student data:', data)
        setStudentData(data)
      }
    } catch (error) {
      console.error('Error fetching student data:', error)
    }
  }

  // Fetch available subjects (only from student's course through course_subject)
  const fetchSubjects = async () => {
    try {
      setLoading(true)
      if (!studentData?.course_id) {
        setSubjects([])
        message.info('Không tìm thấy thông tin khóa học của sinh viên')
        return
      }

      // First, get all course_subjects and filter by course_id
      const courseSubjectResponse = await fetch(`http://localhost:8000/api/course-subjects/`)
      if (!courseSubjectResponse.ok) {
        setSubjects([])
        message.error('Không thể tải danh sách học phần cho khóa học')
        return
      }

      const allCourseSubjects = await courseSubjectResponse.json()
      console.log('All course subjects:', allCourseSubjects)

      // Filter course_subjects by student's course_id
      const courseSubjects = allCourseSubjects.filter((cs: any) => cs.course_id === studentData.course_id)
      console.log('Filtered course subjects for course_id', studentData.course_id, ':', courseSubjects)

      if (!courseSubjects || courseSubjects.length === 0) {
        setSubjects([])
        message.info('Khóa học chưa có học phần nào được thiết lập')
        return
      }

      // Get detailed subject information for each subject_id in course_subjects
      const subjectDetails = await Promise.all(
        courseSubjects.map(async (courseSubject: any) => {
          try {
            const response = await fetch(`http://localhost:8000/api/subjects/${courseSubject.subject_id}`)
            if (response.ok) {
              const subjectData = await response.json()
              // Add course_subject info to subject data
              return {
                ...subjectData,
                learning_semester: courseSubject.learning_semester,
                course_subject_id: courseSubject.id
              }
            }
            return null
          } catch (error) {
            console.error(`Error fetching subject ${courseSubject.subject_id}:`, error)
            return null
          }
        })
      )

      const validSubjects = subjectDetails.filter(subject => subject !== null)
      console.log('Valid subjects:', validSubjects)
      setSubjects(validSubjects)
      
      if (validSubjects.length === 0) {
        message.info('Không tìm thấy học phần hợp lệ cho khóa học của bạn')
      }
    } catch (error) {
      console.error('Error fetching subjects:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Fetch registered subjects
  const fetchRegisteredSubjects = async () => {
    if (!userInfo?.id) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/subject-registers/student/${userInfo.id}`)
      if (response.ok) {
        const registersData = await response.json()
        console.log('Registered subjects data:', registersData)
        
        // Fetch subject information for each registered subject
        const subjectsResponse = await fetch('http://localhost:8000/api/subjects/')
        if (subjectsResponse.ok) {
          const allSubjects = await subjectsResponse.json()
          
          // Join subject info with register data
          const enrichedRegisters = registersData.map((register: any) => {
            const subjectInfo = allSubjects.find((subject: any) => subject.id === register.subject_id)
            return {
              ...register,
              subject_id: subjectInfo?.subject_id || 'N/A', // Using subject.subject_id as subject code
              subject_name: subjectInfo?.subject_name || register.subject_name || 'N/A',
              credits: subjectInfo?.credits || register.credits || 0
            }
          })
          
          console.log('Enriched registered subjects:', enrichedRegisters)
          setRegisteredSubjects(enrichedRegisters)
        } else {
          setRegisteredSubjects(registersData)
        }
      } else {
        console.error('Failed to fetch registered subjects, status:', response.status)
        message.error('Không thể tải danh sách học phần đã đăng ký')
      }
    } catch (error) {
      console.error('Error fetching registered subjects:', error)
      message.error('Lỗi kết nối server')
    }
  }

  // Register for subject
  const registerSubject = async (subjectId: number) => {
    if (!studentData?.id) {
      message.error('Không tìm thấy thông tin sinh viên')
      return
    }

    try {
      setLoading(true)
      console.log('Registering subject with student_id:', studentData.id, 'subject_id:', subjectId)
      const response = await fetch('http://localhost:8000/api/subject-registers/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: studentData.id,
          subject_id: subjectId
        }),
      })

      if (response.ok) {
        message.success('Đăng ký học phần thành công!')
        setModalVisible(false)
        setSelectedSubject(null)
        // Refresh both lists
        await fetchSubjects()
        await fetchRegisteredSubjects()
      } else {
        const errorData = await response.json()
        message.error(errorData.detail || 'Đăng ký thất bại')
      }
    } catch (error) {
      console.error('Error registering subject:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Cancel registration
  const cancelRegistration = async (registerId: number) => {
    try {
      setLoading(true)
      console.log('Deleting subject register with ID:', registerId)
      const response = await fetch(`http://localhost:8000/api/subject-registers/${registerId}`, {
        method: 'DELETE'
      })

      console.log('Delete response status:', response.status)
      if (response.ok) {
        message.success('Hủy đăng ký thành công!')
        // Refresh both lists
        await fetchSubjects()
        await fetchRegisteredSubjects()
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        console.error('Delete error:', errorData)
        message.error(errorData.detail || 'Hủy đăng ký thất bại')
      }
    } catch (error) {
      console.error('Error canceling registration:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStudentData()
  }, [userInfo])

  useEffect(() => {
    if (studentData) {
      fetchSubjects()
      fetchRegisteredSubjects()
    }
  }, [studentData])

  // Filter subjects
  const filteredSubjects = useMemo(() => {
    return subjects.filter(subject => {
      // Safe string matching with null/undefined checks
      const subjectName = subject.subject_name || ''
      const subjectCode = subject.subject_id || ''
      const searchLower = searchText.toLowerCase()
      
      const matchSearch = searchText === '' || 
                         subjectName.toLowerCase().includes(searchLower) ||
                         subjectCode.toLowerCase().includes(searchLower)
      
      const matchSemester = filterSemester === null || subject.semester === filterSemester
      const matchType = filterType === null || subject.subject_type === filterType
      
      // Check if already registered
      const isRegistered = registeredSubjects.some(reg => reg.subject_id === subject.id)
      
      return matchSearch && matchSemester && matchType && !isRegistered
    })
  }, [subjects, searchText, filterSemester, filterType, registeredSubjects])

  const availableSubjectsColumns = [
    {
      title: 'Mã học phần',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 120,
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Tên học phần',
      dataIndex: 'subject_name',
      key: 'subject_name',
      render: (text: string) => (
        <div className="flex items-center">
          <BookOutlined className="mr-2 text-blue-500" />
          {text}
        </div>
      )
    },
    {
      title: 'Số tín chỉ',
      dataIndex: 'credits',
      key: 'credits',
      width: 100,
      align: 'center' as const,
      render: (credits: number) => (
        <Tag color="blue">{credits} TC</Tag>
      )
    },
    {
      title: 'Học kỳ',
      key: 'newest_semester',
      width: 100,
      align: 'center' as const,
      render: () => (
        <Tag color="green">HK {studentData?.newest_semester || 'N/A'}</Tag>
      )
    },
    
    {
      title: 'Thao tác',
      key: 'action',
      width: 120,
      align: 'center' as const,
      render: (_: any, record: Subject) => (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="small"
          onClick={() => {
            setSelectedSubject(record)
            setModalVisible(true)
          }}
        >
          Đăng ký
        </Button>
      ),
    },
  ]

  const registeredSubjectsColumns = [
    {
      title: 'Mã học phần',
      dataIndex: 'subject_id',
      key: 'subject_id',
      width: 120,
      render: (code: string | number) => <Text strong>{code}</Text>
    },
    {
      title: 'Tên học phần',
      dataIndex: 'subject_name',
      key: 'subject_name',
      render: (text: string) => (
        <div className="flex items-center">
          <BookOutlined className="mr-2 text-green-500" />
          {text}
        </div>
      )
    },
    {
      title: 'Số tín chỉ',
      dataIndex: 'credits',
      key: 'credits',
      width: 100,
      align: 'center' as const,
      render: (credits: number) => (
        <Tag color="blue">{credits} TC</Tag>
      )
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'register_date',
      key: 'register_date',
      width: 160,
      render: (date: string) => {
        if (!date) return 'N/A'
        try {
          const dateObj = new Date(date)
          return (
            <div className="flex items-center">
              <CalendarOutlined className="mr-1" />
              <div>
                <div>{dateObj.toLocaleDateString('vi-VN')}</div>
                <div className="text-xs text-gray-500">
                  {dateObj.toLocaleTimeString('vi-VN')}
                </div>
              </div>
            </div>
          )
        } catch (error) {
          return 'Invalid Date'
        }
      }
    },
    {
      title: 'Thao tác',
      key: 'action',
      width: 120,
      align: 'center' as const,
      render: (_: any, record: SubjectRegister) => (
        <Button
          danger
          size="small"
          onClick={() => {
            console.log('Cancel button clicked for record:', record)
            const confirmResult = window.confirm(`Bạn có chắc chắn muốn hủy đăng ký học phần "${record.subject_name}"?`)
            if (confirmResult) {
              console.log('User confirmed, calling cancelRegistration with ID:', record.id)
              cancelRegistration(record.id)
            }
          }}
        >
          Hủy
        </Button>
      ),
    },
  ]

  const totalCredits = registeredSubjects.reduce((sum, subject) => sum + subject.credits, 0)

  return (
    <div className="space-y-6">
      
      {/* Summary Card */}
      <Card size="small">
        <div className="flex justify-between items-center">
          <div>
            <Text strong>Tổng số học phần đã đăng ký: </Text>
            <Tag color="blue" className="ml-2">{registeredSubjects.length} học phần</Tag>
          </div>
          <div>
            <Text strong>Tổng số tín chỉ: </Text>
            <Tag color="green" className="ml-2">{totalCredits} TC</Tag>
          </div>
        </div>
      </Card>

      {/* Registered Subjects */}
      <Card 
        title="Học phần đã đăng ký" 
        extra={<Tag color="green">{registeredSubjects.length} học phần</Tag>}
      >
        <Table
          columns={registeredSubjectsColumns}
          dataSource={registeredSubjects}
          rowKey="id"
          size="small"
          pagination={false}
          locale={{ emptyText: 'Chưa có học phần nào được đăng ký' }}
        />
      </Card>

      {/* Available Subjects */}
      <Card 
        title="Danh sách học phần có thể đăng ký"
        extra={
          <Space>
            <Input
              placeholder="Tìm kiếm học phần..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => {
                const value = e.target.value || ''
                setSearchText(value)
              }}
              style={{ width: 200 }}
              allowClear
            />
            
            
          </Space>
        }
      >
        <Table
          columns={availableSubjectsColumns}
          dataSource={filteredSubjects}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Tổng ${total} học phần`
          }}
        />
      </Card>

      {/* Confirmation Modal */}
      <Modal
        title="Xác nhận đăng ký học phần"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setSelectedSubject(null)
        }}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            Hủy
          </Button>,
          <Button
            key="confirm"
            type="primary"
            loading={loading}
            onClick={() => selectedSubject && registerSubject(selectedSubject.id)}
          >
            Xác nhận đăng ký
          </Button>,
        ]}
      >
        {selectedSubject && (
          <div className="space-y-3">
            <div>
              <Text strong>Mã học phần: </Text>
              <Text>{selectedSubject.subject_id}</Text>
            </div>
            <div>
              <Text strong>Tên học phần: </Text>
              <Text>{selectedSubject.subject_name}</Text>
            </div>
            <div>
              <Text strong>Số tín chỉ: </Text>
              <Tag color="blue">{selectedSubject.credits} TC</Tag>
            </div>
            <div>
              <Text strong>Học kỳ: </Text>
              <Tag color="green">HK {selectedSubject.semester}</Tag>
            </div>
            
            {selectedSubject.description && (
              <div>
                <Text strong>Mô tả: </Text>
                <Text>{selectedSubject.description}</Text>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SubjectRegistration