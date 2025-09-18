import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Table, Modal, message, Space, Tag, Typography, Card, Input, Select } from 'antd'
import { SearchOutlined, HomeOutlined, PlusOutlined, CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons'

const { Text } = Typography
const { Option } = Select

interface Class {
  id: number
  class_name: string
  class_code: string
  instructor_name: string
  room: string
  time_slot: string
  max_students: number
  current_students: number
  subject_id: number
  subject_name: string
  credits: number
  status: string
}

interface ClassRegister {
  id: number
  student_id: number
  class_id: number
  class_info: string
  register_type: string
  register_status: string
  register_date: string
}

const ClassRegistration = () => {
  const { userInfo } = useAuth()
  const [classes, setClasses] = useState<Class[]>([])
  const [registeredClasses, setRegisteredClasses] = useState<ClassRegister[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedClass, setSelectedClass] = useState<Class | null>(null)
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)
  const [registeredSubjectIds, setRegisteredSubjectIds] = useState<number[]>([])

  // Fetch registered subject IDs for current student
  const fetchRegisteredSubjectIds = async () => {
    if (!userInfo?.student_id) return
    
    try {
      // Use student-mssv endpoint with MSSV
      const response = await fetch(`http://localhost:8000/subject-registers/student-mssv/${userInfo.student_id}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Registered subjects data:', data)
        const subjectIds = data.map((reg: any) => reg.subject_id)
        setRegisteredSubjectIds(subjectIds)
      }
    } catch (error) {
      console.error('Error fetching registered subjects:', error)
    }
  }

  // Fetch available classes (only for subjects student registered)
  const fetchClasses = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/classes/')
      if (response.ok) {
        const allClasses = await response.json()
        // Filter classes to only show those with subject_id in registered subjects
        const allowedClasses = allClasses.filter((classItem: Class) => 
          registeredSubjectIds.includes(classItem.subject_id)
        )
        setClasses(allowedClasses)
      } else {
        message.error('Không thể tải danh sách lớp học')
      }
    } catch (error) {
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Fetch registered classes
  const fetchRegisteredClasses = async () => {
    if (!userInfo?.student_id) return
    
    try {
      // Use student-mssv endpoint with MSSV
      const response = await fetch(`http://localhost:8000/class-registers/student/${userInfo.student_id}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Registered classes data:', data)
        setRegisteredClasses(data)
      } else {
        console.error('Failed to fetch registered classes, status:', response.status)
      }
    } catch (error) {
      console.error('Error fetching registered classes:', error)
    }
  }

  // Register for class
  const registerClass = async (classId: number) => {
    if (!userInfo?.student_id) {
      message.error('Không tìm thấy thông tin sinh viên')
      return
    }

    try {
      setLoading(true)
      console.log('Registering class with data:', {
        student_id: userInfo.student_id,
        class_id: classId,
        class_info: selectedClass?.class_name || '',
        register_type: 'Bình thường',
        register_status: 'Đang chờ'
      })
      
      const response = await fetch('http://localhost:8000/class-registers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: userInfo.student_id,
          class_id: classId,
          class_info: selectedClass?.class_name || '',
          register_type: 'Bình thường',
          register_status: 'Đang chờ'
        }),
      })

      if (response.ok) {
        message.success('Đăng ký lớp học thành công!')
        setModalVisible(false)
        setSelectedClass(null)
        // Refresh both lists
        await fetchClasses()
        await fetchRegisteredClasses()
      } else {
        const errorData = await response.json()
        console.error('Registration failed:', errorData)
        message.error(errorData.detail || 'Đăng ký thất bại')
      }
    } catch (error) {
      console.error('Error registering class:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Cancel registration
  const cancelRegistration = async (registerId: number) => {
    console.log('Attempting to cancel registration with ID:', registerId)
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/class-registers/${registerId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        message.success('Hủy đăng ký thành công!')
        // Refresh both lists
        await fetchClasses()
        await fetchRegisteredClasses()
      } else {
        console.error('Failed to cancel registration, status:', response.status)
        message.error('Hủy đăng ký thất bại')
      }
    } catch (error) {
      console.error('Error cancelling registration:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (userInfo?.student_id) {
      fetchRegisteredSubjectIds()
    }
  }, [userInfo])

  useEffect(() => {
    if (registeredSubjectIds.length >= 0) { // Allow empty array to show "no data"
      fetchClasses()
      fetchRegisteredClasses()
    }
  }, [registeredSubjectIds])

  // Filter classes safely
  const filteredClasses = classes.filter(classItem => {
    const searchLower = (searchText || '').toLowerCase()
    const matchSearch = searchLower === '' ||
                       (classItem.class_name || '').toLowerCase().includes(searchLower) ||
                       (classItem.class_code || '').toLowerCase().includes(searchLower) ||
                       (classItem.subject_name || '').toLowerCase().includes(searchLower) ||
                       (classItem.instructor_name || '').toLowerCase().includes(searchLower)
    const matchStatus = filterStatus === null || (classItem.status || '') === filterStatus
    
    // Check if already registered
    const isRegistered = registeredClasses.some(reg => reg.class_id === classItem.id)
    
    return matchSearch && matchStatus && !isRegistered
  })

  const availableClassesColumns = [
    {
      title: 'Mã lớp',
      dataIndex: 'class_code',
      key: 'class_code',
      width: 100,
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Tên lớp',
      dataIndex: 'class_name',
      key: 'class_name',
      render: (text: string) => (
        <div className="flex items-center">
          <HomeOutlined className="mr-2 text-blue-500" />
          {text}
        </div>
      )
    },
    {
      title: 'Học phần',
      key: 'subject_info',
      render: (record: Class) => (
        <div>
          <div>{record.subject_name || 'N/A'}</div>
          <Tag color="blue">{record.credits || 0} TC</Tag>
        </div>
      )
    },
    {
      title: 'Giảng viên',
      dataIndex: 'instructor_name',
      key: 'instructor_name',
      width: 150,
      render: (text: string) => text || 'Chưa phân công'
    },
    {
      title: 'Phòng học',
      dataIndex: 'room',
      key: 'room',
      width: 100,
      render: (room: string) => (
        <Tag color="green">{room || 'Chưa phân phòng'}</Tag>
      )
    },
    {
      title: 'Thời gian',
      dataIndex: 'time_slot',
      key: 'time_slot',
      width: 120,
      render: (time: string) => (
        <div className="flex items-center">
          <ClockCircleOutlined className="mr-1" />
          <span className="text-sm">{time || 'Chưa xác định'}</span>
        </div>
      )
    },
    {
      title: 'Sĩ số',
      key: 'students',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: Class) => (
        <div>
          <Text>{record.current_students || 0}/{record.max_students || 0}</Text>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
            <div 
              className="bg-blue-600 h-2 rounded-full" 
              style={{ 
                width: `${record.max_students > 0 ? (record.current_students / record.max_students) * 100 : 0}%` 
              }}
            ></div>
          </div>
        </div>
      )
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'Mở' ? 'green' : status === 'Đầy' ? 'red' : 'orange'}>
          {status || 'Chưa xác định'}
        </Tag>
      )
    },
    {
      title: 'Thao tác',
      key: 'action',
      width: 120,
      align: 'center' as const,
      render: (_: any, record: Class) => (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="small"
          disabled={record.status !== 'Mở' || record.current_students >= record.max_students}
          onClick={() => {
            setSelectedClass(record)
            setModalVisible(true)
          }}
        >
          Đăng ký
        </Button>
      ),
    },
  ]

  const registeredClassesColumns = [
    {
      title: 'Thông tin lớp',
      dataIndex: 'class_info',
      key: 'class_info',
      render: (text: string) => (
        <div className="flex items-center">
          <HomeOutlined className="mr-2 text-green-500" />
          {text}
        </div>
      )
    },
    {
      title: 'Loại đăng ký',
      dataIndex: 'register_type',
      key: 'register_type',
      width: 120,
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      )
    },
    {
      title: 'Trạng thái',
      dataIndex: 'register_status',
      key: 'register_status',
      width: 120,
      render: (status: string) => (
        <Tag color={status === 'Đã duyệt' ? 'green' : status === 'Đã từ chối' ? 'red' : 'orange'}>
          {status}
        </Tag>
      )
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'register_date',
      key: 'register_date',
      width: 130,
      render: (date: string) => (
        <div className="flex items-center">
          <CalendarOutlined className="mr-1" />
          {new Date(date).toLocaleDateString('vi-VN')}
        </div>
      )
    },
    {
      title: 'Thao tác',
      key: 'action',
      width: 120,
      align: 'center' as const,
      render: (_: any, record: ClassRegister) => (
        <Button
          danger
          size="small"
          disabled={record.register_status === 'Đã duyệt'}
          onClick={() => {
            console.log('Cancel button clicked for record:', record)
            const confirmResult = window.confirm(`Bạn có chắc chắn muốn hủy đăng ký lớp "${record.class_info}"?`)
            if (confirmResult) {
              console.log('User confirmed, calling cancelRegistration with ID:', record.id)
              cancelRegistration(record.id)
            }
          }}
        >
          {record.register_status === 'Đã duyệt' ? 'Không thể hủy' : 'Hủy'}
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card size="small">
        <div className="flex justify-between items-center">
          <div>
            <Text strong>Tổng số lớp đã đăng ký: </Text>
            <Tag color="blue" className="ml-2">{registeredClasses.length} lớp</Tag>
          </div>
          <div>
            <Text strong>Lớp được duyệt: </Text>
            <Tag color="green" className="ml-2">
              {registeredClasses.filter(c => c.register_status === 'Đã duyệt').length} lớp
            </Tag>
          </div>
        </div>
      </Card>

      {/* Registered Classes */}
      <Card 
        title="Lớp học đã đăng ký" 
        extra={<Tag color="green">{registeredClasses.length} lớp</Tag>}
      >
        <Table
          columns={registeredClassesColumns}
          dataSource={registeredClasses}
          rowKey="id"
          size="small"
          pagination={false}
          locale={{ emptyText: 'Chưa có lớp học nào được đăng ký' }}
        />
      </Card>

      {/* Available Classes */}
      <Card 
        title="Danh sách lớp học có thể đăng ký"
        extra={
          <Space>
            <Input
              placeholder="Tìm kiếm lớp học..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => {
                const value = e.target.value || ''
                setSearchText(value)
              }}
              style={{ width: 250 }}
              allowClear
            />
            <Select
              placeholder="Trạng thái"
              allowClear
              style={{ width: 120 }}
              value={filterStatus}
              onChange={setFilterStatus}
            >
              <Option value="Mở">Mở</Option>
              <Option value="Đầy">Đầy</Option>
              <Option value="Đóng">Đóng</Option>
            </Select>
          </Space>
        }
      >
        {registeredSubjectIds.length === 0 ? (
          <div className="text-center py-8">
            <Text type="secondary">
              Bạn chưa đăng ký học phần nào. Vui lòng đăng ký học phần trước khi đăng ký lớp.
            </Text>
          </div>
        ) : (
          <Table
            columns={availableClassesColumns}
            dataSource={filteredClasses}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `Tổng ${total} lớp học`
            }}
            scroll={{ x: 1200 }}
          />
        )}
      </Card>

      {/* Confirmation Modal */}
      <Modal
        title="Xác nhận đăng ký lớp học"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setSelectedClass(null)
        }}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            Hủy
          </Button>,
          <Button
            key="confirm"
            type="primary"
            loading={loading}
            onClick={() => selectedClass && registerClass(selectedClass.id)}
          >
            Xác nhận đăng ký
          </Button>,
        ]}
      >
        {selectedClass && (
          <div className="space-y-3">
            <div>
              <Text strong>Mã lớp: </Text>
              <Text>{selectedClass.class_code}</Text>
            </div>
            <div>
              <Text strong>Tên lớp: </Text>
              <Text>{selectedClass.class_name}</Text>
            </div>
            <div>
              <Text strong>Học phần: </Text>
              <Text>{selectedClass.subject_name || 'N/A'}</Text>
              <Tag color="blue" className="ml-2">{selectedClass.credits || 0} TC</Tag>
            </div>
            <div>
              <Text strong>Giảng viên: </Text>
              <Text>{selectedClass.instructor_name || 'Chưa phân công'}</Text>
            </div>
            <div>
              <Text strong>Phòng học: </Text>
              <Tag color="green">{selectedClass.room || 'Chưa phân phòng'}</Tag>
            </div>
            <div>
              <Text strong>Thời gian: </Text>
              <Text>{selectedClass.time_slot || 'Chưa xác định'}</Text>
            </div>
            <div>
              <Text strong>Sĩ số hiện tại: </Text>
              <Text>{selectedClass.current_students || 0}/{selectedClass.max_students || 0} sinh viên</Text>
            </div>
            <div>
              <Text strong>Trạng thái: </Text>
              <Tag color={selectedClass.status === 'Mở' ? 'green' : 'red'}>
                {selectedClass.status || 'Chưa xác định'}
              </Tag>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ClassRegistration