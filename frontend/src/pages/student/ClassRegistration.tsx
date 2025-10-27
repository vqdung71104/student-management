import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Table, Modal, message, Space, Tag, Typography, Card, Input, Select } from 'antd'
import { SearchOutlined, HomeOutlined, PlusOutlined, CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons'

const { Text } = Typography
const { Option } = Select

interface Class {
  id: number
  class_id: number
  class_name: string
  class_code: string
  class_type: string
  instructor_name?: string
  teacher_name?: string
  room?: string
  classroom?: string
  time_slot?: string
  study_date?: string
  study_time_start?: string
  study_time_end?: string
  max_students?: number
  max_student_number?: number
  current_students: number
  registered_count?: number // Add this field for actual registered students
  subject_id: number
  subject_name?: string
  credits?: number
  status: string
  linked_class_ids?: number[]
  subject?: {
    subject_name: string
    credits: number
  }
}

interface ClassRegister {
  id: number
  student_id: number
  class_id: number
  class_info: string
  register_type: string
  register_status: string
  register_date: string
  // Added fields from enriched data
  class_name?: string
  class_code?: string | number
  subject_name?: string
  classroom?: string
  teacher_name?: string
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
    if (!userInfo?.id) return
    
    try {
      // Use student ID endpoint
      const response = await fetch(`http://localhost:8000/subject-registers/student/${userInfo.id}`)
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
        console.log('All classes fetched:', allClasses.length)
        
        // Fetch registration counts for all classes
        const registrationResponse = await fetch('http://localhost:8000/class-registers/')
        let registrationCounts: { [key: number]: number } = {}
        
        if (registrationResponse.ok) {
          const allRegistrations = await registrationResponse.json()
          // Count registrations by class_id (which is the foreign key to class.id)
          registrationCounts = allRegistrations.reduce((acc: { [key: number]: number }, reg: any) => {
            acc[reg.class_id] = (acc[reg.class_id] || 0) + 1
            return acc
          }, {})
          console.log('Registration counts:', registrationCounts)
        }
        
        // Add registration count to each class
        const classesWithCounts = allClasses.map((classItem: any) => ({
          ...classItem,
          registered_count: registrationCounts[classItem.id] || 0
        }))
        
        // Create a Set of all linked class IDs to filter out
        const linkedClassIds = new Set<number>()
        classesWithCounts.forEach((classItem: any) => {
          if (classItem.linked_class_ids && Array.isArray(classItem.linked_class_ids)) {
            classItem.linked_class_ids.forEach((linkedId: number) => {
              if (linkedId !== classItem.class_id) { // Don't exclude self
                linkedClassIds.add(linkedId)
              }
            })
          }
        })
        
        console.log('Linked class IDs to exclude:', Array.from(linkedClassIds))
        
        // Filter classes: must be in registered subjects AND not be a linked class
        const allowedClasses = classesWithCounts.filter((classItem: any) => {
          const isRegisteredSubject = registeredSubjectIds.includes(classItem.subject?.id)
          const isNotLinkedClass = !linkedClassIds.has(classItem.class_id)
          return isRegisteredSubject && isNotLinkedClass
        })
        
        console.log('Filtered classes (main classes only):', allowedClasses.length)
        setClasses(allowedClasses)
      } else {
        message.error('Không thể tải danh sách lớp học')
      }
    } catch (error) {
      console.error('Error fetching classes:', error)
      message.error('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  // Fetch registered classes
  const fetchRegisteredClasses = async () => {
    if (!userInfo?.id) return
    
    try {
      // Use student ID endpoint
      const response = await fetch(`http://localhost:8000/class-registers/student/${userInfo.id}`)
      if (response.ok) {
        const registersData = await response.json()
        console.log('Registered classes data:', registersData)
        
        // Fetch class information for each registered class
        const classesResponse = await fetch('http://localhost:8000/classes/')
        if (classesResponse.ok) {
          const allClasses = await classesResponse.json()
          
          // Join class info with register data
          const enrichedRegisters = registersData.map((register: any) => {
            const classInfo = allClasses.find((cls: any) => cls.id === register.class_id)
            return {
              ...register,
              class_name: classInfo?.class_name || 'Unknown',
              class_code: classInfo?.class_id || 'N/A',
              subject_name: classInfo?.subject?.subject_name || 'N/A',
              classroom: classInfo?.classroom || 'N/A',
              teacher_name: classInfo?.teacher_name || 'N/A'
            }
          })
          
          console.log('Enriched registered classes:', enrichedRegisters)
          setRegisteredClasses(enrichedRegisters)
        } else {
          setRegisteredClasses(registersData)
        }
      } else {
        console.error('Failed to fetch registered classes, status:', response.status)
      }
    } catch (error) {
      console.error('Error fetching registered classes:', error)
    }
  }

  // Register for class
  const registerClass = async (classId: number) => {
    if (!userInfo?.id) {
      message.error('Không tìm thấy thông tin sinh viên')
      return
    }

    try {
      setLoading(true)
      
      // Find the selected class to get its linked classes
      const selectedClassData = classes.find(cls => cls.id === classId)
      const linkedClassIds = selectedClassData?.linked_class_ids || []
      
      console.log('Main class ID:', classId)
      console.log('Main class data:', selectedClassData)
      console.log('Linked class IDs (class_id values):', linkedClassIds)

      // Register main class
      const registerData = {
        student_id: userInfo.id,
        class_id: classId,
        class_info: 'Đang mở',
        register_type: 'Đăng ký online',
        register_status: 'Đăng ký thành công'
      }

      console.log('Registering main class:', registerData)
      
      const response = await fetch('http://localhost:8000/class-registers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Đăng ký lớp chính thất bại')
      }

      // Register linked classes if any
      // Need to fetch all classes to find linked classes (since they're filtered out from main list)
      const linkedRegistrations = []
      if (linkedClassIds.length > 0) {
        console.log('Fetching all classes to find linked classes...')
        const allClassesResponse = await fetch('http://localhost:8000/classes/')
        if (allClassesResponse.ok) {
          const allClasses = await allClassesResponse.json()
          
          for (const linkedClassId of linkedClassIds) {
            if (linkedClassId !== selectedClassData?.class_id) { // Don't register self again
              // Find the class with this class_id to get its database id
              const linkedClass = allClasses.find((cls: any) => cls.class_id === linkedClassId)
              if (linkedClass) {
                const linkedRegisterData = {
                  student_id: userInfo.id,
                  class_id: linkedClass.id, // Use database ID, not class_id
                  class_info: 'Đang mở',
                  register_type: 'Đăng ký online',
                  register_status: 'Đăng ký thành công'
                }

                console.log(`Registering linked class ${linkedClassId} (DB ID: ${linkedClass.id}):`, linkedRegisterData)
                
                const linkedResponse = await fetch('http://localhost:8000/class-registers', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(linkedRegisterData),
                })

                if (linkedResponse.ok) {
                  linkedRegistrations.push(linkedClassId)
                } else {
                  const errorData = await linkedResponse.json()
                  console.warn(`Failed to register linked class ${linkedClassId}:`, errorData)
                }
              } else {
                console.warn(`Could not find linked class with class_id ${linkedClassId} in all classes`)
              }
            }
          }
        } else {
          console.error('Failed to fetch all classes for linked class registration')
        }
      }

      const totalRegistered = 1 + linkedRegistrations.length
      message.success(`Đăng ký thành công ${totalRegistered} lớp học!${linkedRegistrations.length > 0 ? ` (Bao gồm ${linkedRegistrations.length} lớp kèm)` : ''}`)
      
      setModalVisible(false)
      setSelectedClass(null)
      // Refresh both lists
      await fetchClasses()
      await fetchRegisteredClasses()
      
    } catch (error) {
      console.error('Error registering class:', error)
      message.error(error instanceof Error ? error.message : 'Lỗi kết nối server')
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
    if (userInfo?.id) {
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
      key: 'class_id',
      width: 80,
      render: (record: any) => <Text strong>{record.class_id || 'N/A'}</Text>
    },
    {
      title: 'Học phần',
      key: 'class_name',
      width: 180,
      render: (record: any) => (
        <div>
          <div className="font-medium">{record.class_name || 'N/A'}</div>
          <div className="text-xs text-gray-500">{record.subject?.subject_name || 'N/A'}</div>
        </div>
      )
    },
    {
      title: 'Lớp kèm',
      key: 'linked_classes',
      width: 90,
      render: (record: any) => {
        const linkedIds = record.linked_class_ids || []
        return linkedIds.length > 0 ? (
          <div className="text-xs">
            {linkedIds.slice(0, 2).map((id: number) => (
              <div key={id}>{id}</div>
            ))}
            {linkedIds.length > 2 && <div>+{linkedIds.length - 2}</div>}
          </div>
        ) : 'Không'
      }
    },
    {
      title: 'Loại',
      dataIndex: 'class_type',
      key: 'class_type',
      width: 70,
      render: (type: string) => (
        <Tag color="blue">{type || 'N/A'}</Tag>
      )
    },
    {
      title: 'Phòng',
      dataIndex: 'classroom',
      key: 'classroom',
      width: 80,
      render: (room: string) => (
        <Tag color="green">{room || 'TBD'}</Tag>
      )
    },
    {
      title: 'Thời gian',
      key: 'schedule',
      width: 120,
      render: (record: any) => (
        <div className="text-xs">
          <div>{record.study_date || 'N/A'}</div>
          <div className="text-gray-500">
            {record.study_time_start} - {record.study_time_end}
          </div>
        </div>
      )
    },
    {
      title: 'Sĩ số',
      key: 'capacity',
      width: 70,
      align: 'center' as const,
      render: (record: any) => {
        const registeredCount = record.registered_count || 0
        const maxStudents = record.max_student_number || 0
        const percentage = maxStudents > 0 ? (registeredCount / maxStudents) * 100 : 0
        
        return (
          <div className="text-center">
            <div className="text-sm">{registeredCount}/{maxStudents}</div>
            <div className="w-full bg-gray-200 rounded h-1 mt-1">
              <div 
                className={`h-1 rounded ${percentage >= 100 ? 'bg-red-500' : percentage >= 80 ? 'bg-orange-500' : 'bg-blue-500'}`}
                style={{ width: `${Math.min(percentage, 100)}%` }}
              ></div>
            </div>
          </div>
        )
      }
    },
    {
      title: 'Thao tác',
      key: 'action',
      width: 90,
      align: 'center' as const,
      render: (_: any, record: any) => (
        <Button
          type="primary"
          size="small"
          onClick={() => {
            console.log('Register button clicked for class:', record)
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
      key: 'class_details',
      render: (record: ClassRegister) => (
        <div>
          <div className="flex items-center mb-1">
            <HomeOutlined className="mr-2 text-green-500" />
            <strong>{record.class_name || record.class_info}</strong>
          </div>
          <div className="text-sm text-gray-500">
            Mã lớp: {record.class_code || 'N/A'} | Học phần: {record.subject_name || 'N/A'}
          </div>
          <div className="text-sm text-gray-500">
            Phòng: {record.classroom || 'N/A'} | GV: {record.teacher_name || 'N/A'}
          </div>
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
              pageSize: 8,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `Tổng ${total} lớp học`
            }}
            tableLayout="auto"
            scroll={{ y: 400 }}
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
              <Text>{selectedClass.class_id}</Text>
            </div>
            <div>
              <Text strong>Tên lớp: </Text>
              <Text>{selectedClass.class_name}</Text>
            </div>
            <div>
              <Text strong>Học phần: </Text>
              <Text>{selectedClass.subject?.subject_name || 'N/A'}</Text>
              <Tag color="blue" className="ml-2">{selectedClass.subject?.credits || 0} TC</Tag>
            </div>
            <div>
              <Text strong>Loại lớp: </Text>
              <Tag color="blue">{selectedClass.class_type || 'N/A'}</Tag>
            </div>
            <div>
              <Text strong>Giảng viên: </Text>
              <Text>{selectedClass.teacher_name || 'Chưa phân công'}</Text>
            </div>
            <div>
              <Text strong>Phòng học: </Text>
              <Tag color="green">{selectedClass.classroom || 'Chưa phân phòng'}</Tag>
            </div>
            <div>
              <Text strong>Thời gian: </Text>
              <Text>
                {selectedClass.study_date} ({selectedClass.study_time_start} - {selectedClass.study_time_end})
              </Text>
            </div>
            <div>
              <Text strong>Lớp kèm: </Text>
              <Text>
                {selectedClass.linked_class_ids && selectedClass.linked_class_ids?.length > 0
                  ? selectedClass.linked_class_ids.join(', ')
                  : 'Không có'
                }
              </Text>
            </div>
            <div>
              <Text strong>Sĩ số hiện tại: </Text>
              <Text>0/{selectedClass.max_student_number || 0} sinh viên</Text>
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