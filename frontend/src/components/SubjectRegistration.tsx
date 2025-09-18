import { useState, useEffect } from 'react'
import { Button, Table, Modal, message, Space, Tag, Typography, Card, Input, Select } from 'antd'
import { SearchOutlined, BookOutlined, PlusOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { Option } = Select

interface Subject {
  id: number
  subject_name: string
  subject_code: string
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

interface StudentInfo {
  student_id: number
  student_name: string
  mssv: string
  email: string
  class_name: string
  department_name: string
}

interface SubjectRegistrationProps {
  studentInfo: StudentInfo
}

const SubjectRegistration = ({ studentInfo }: SubjectRegistrationProps) => {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [registeredSubjects, setRegisteredSubjects] = useState<SubjectRegister[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [searchText, setSearchText] = useState('')
  const [filterSemester, setFilterSemester] = useState<number | null>(null)
  const [filterType, setFilterType] = useState<string | null>(null)

  // Fetch available subjects
  const fetchSubjects = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/subjects/')
      if (response.ok) {
        const data = await response.json()
        setSubjects(data)
      } else {
        message.error('Không thể tải danh sách học phần')
      }
    } catch (error) {
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Fetch registered subjects
  const fetchRegisteredSubjects = async () => {
    try {
      const response = await fetch(`http://localhost:8000/subject-registers/student/${studentInfo.student_id}`)
      if (response.ok) {
        const data = await response.json()
        setRegisteredSubjects(data)
      } else {
        message.error('Không thể tải danh sách học phần đã đăng ký')
      }
    } catch (error) {
      message.error('Lỗi kết nối server')
    }
  }

  // Register for subject
  const registerSubject = async (subjectId: number) => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/subject-registers/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: studentInfo.student_id,
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
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Cancel registration
  const cancelRegistration = async (registerId: number) => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/subject-registers/${registerId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        message.success('Hủy đăng ký thành công!')
        // Refresh both lists
        await fetchSubjects()
        await fetchRegisteredSubjects()
      } else {
        message.error('Hủy đăng ký thất bại')
      }
    } catch (error) {
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubjects()
    fetchRegisteredSubjects()
  }, [studentInfo.student_id])

  // Filter subjects
  const filteredSubjects = subjects.filter(subject => {
    const matchSearch = subject.subject_name.toLowerCase().includes(searchText.toLowerCase()) ||
                       subject.subject_code.toLowerCase().includes(searchText.toLowerCase())
    const matchSemester = filterSemester === null || subject.semester === filterSemester
    const matchType = filterType === null || subject.subject_type === filterType
    
    // Check if already registered
    const isRegistered = registeredSubjects.some(reg => reg.subject_id === subject.id)
    
    return matchSearch && matchSemester && matchType && !isRegistered
  })

  const availableSubjectsColumns = [
    {
      title: 'Mã học phần',
      dataIndex: 'subject_code',
      key: 'subject_code',
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
      dataIndex: 'semester',
      key: 'semester',
      width: 100,
      align: 'center' as const,
      render: (semester: number) => (
        <Tag color="green">HK {semester}</Tag>
      )
    },
    {
      title: 'Loại học phần',
      dataIndex: 'subject_type',
      key: 'subject_type',
      width: 130,
      render: (type: string) => (
        <Tag color={type === 'Bắt buộc' ? 'red' : 'orange'}>{type}</Tag>
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
      key: 'subject_code',
      width: 120,
      render: (_: any, record: SubjectRegister) => {
        const subject = subjects.find(s => s.id === record.subject_id)
        return <Text strong>{subject?.subject_code}</Text>
      }
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
      width: 130,
      render: (date: string) => new Date(date).toLocaleDateString('vi-VN')
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
            Modal.confirm({
              title: 'Xác nhận hủy đăng ký',
              content: `Bạn có chắc chắn muốn hủy đăng ký học phần "${record.subject_name}"?`,
              onOk: () => cancelRegistration(record.id),
            })
          }}
        >
          Hủy
        </Button>
      ),
    },
  ]

  const totalCredits = registeredSubjects.reduce((sum, subject) => sum + subject.credits, 0)

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2} className="flex items-center">
          <BookOutlined className="mr-3 text-blue-600" />
          Đăng ký học phần
        </Title>
        <Text type="secondary">
          Sinh viên: {studentInfo.student_name} - MSSV: {studentInfo.mssv} - Lớp: {studentInfo.class_name}
        </Text>
      </div>

      {/* Summary Card */}
      <Card className="mb-6" size="small">
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
        className="mb-6"
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
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Select
              placeholder="Chọn học kỳ"
              allowClear
              style={{ width: 120 }}
              value={filterSemester}
              onChange={setFilterSemester}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
                <Option key={sem} value={sem}>HK {sem}</Option>
              ))}
            </Select>
            <Select
              placeholder="Loại học phần"
              allowClear
              style={{ width: 140 }}
              value={filterType}
              onChange={setFilterType}
            >
              <Option value="Bắt buộc">Bắt buộc</Option>
              <Option value="Tự chọn">Tự chọn</Option>
            </Select>
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
              <Text>{selectedSubject.subject_code}</Text>
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
            <div>
              <Text strong>Loại học phần: </Text>
              <Tag color={selectedSubject.subject_type === 'Bắt buộc' ? 'red' : 'orange'}>
                {selectedSubject.subject_type}
              </Tag>
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