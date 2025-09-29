import { useState } from 'react'
import FormCard from '../../components/student/FormCard'
import FormModal from '../../components/student/FormModal'
import DocumentPreview from '../../components/student/DocumentPreview'

export interface FormTemplate {
  id: string
  title: string
  description: string
  fullDescription: string
  fields: FormField[]
  documentTemplate: string
}

export interface FormField {
  id: string
  label: string
  type: 'text' | 'email' | 'select' | 'textarea' | 'date'
  required: boolean
  options?: string[]
  placeholder?: string
}

const Forms = () => {
  const [selectedForm, setSelectedForm] = useState<FormTemplate | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [formData, setFormData] = useState<Record<string, string>>({})

  const formTemplates: FormTemplate[] = [
    {
      id: 'bus-card',
      title: 'Đơn đăng ký làm vé thẻ xe buýt',
      description: 'Sinh viên cần làm về thẻ xe buýt cần chuẩn bị đi đơn có đóng 02 ảnh (2x3cm) theo...',
      fullDescription: 'Sinh viên cần làm về thẻ xe buýt cần chuẩn bị đi đơn có đóng 02 ảnh (2x3cm) theo quy định. Thẻ xe buýt dành cho sinh viên với mức giá ưu đãi.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'email', label: 'Email', type: 'email', required: true, placeholder: 'Nhập email' },
        { id: 'phone', label: 'Số điện thoại', type: 'text', required: true, placeholder: 'Nhập số điện thoại' },
        { id: 'address', label: 'Địa chỉ thường trú', type: 'textarea', required: true, placeholder: 'Nhập địa chỉ đầy đủ' },
        { id: 'reason', label: 'Lý do làm thẻ', type: 'select', required: true, options: ['Lần đầu', 'Thẻ cũ hết hạn', 'Thẻ bị mất', 'Thẻ bị hỏng'] }
      ],
      documentTemplate: 'bus-card-template'
    },
    {
      id: 'dormitory-registration',
      title: 'Đơn đăng ký sử dụng phòng học, giảng đường tổ chức các hoạt động của câu...',
      description: 'Đơn xin đăng ký sử dụng phòng học, giảng đường để tổ chức các hoạt động của câu lạc bộ, đoàn thể.',
      fullDescription: 'Đơn xin đăng ký sử dụng phòng học, giảng đường để tổ chức các hoạt động của câu lạc bộ, đoàn thể. Cần đăng ký trước ít nhất 3 ngày.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'organization', label: 'Tên tổ chức/CLB', type: 'text', required: true, placeholder: 'Nhập tên tổ chức' },
        { id: 'eventName', label: 'Tên sự kiện', type: 'text', required: true, placeholder: 'Nhập tên sự kiện' },
        { id: 'eventDate', label: 'Ngày tổ chức', type: 'date', required: true },
        { id: 'room', label: 'Phòng muốn đăng ký', type: 'select', required: true, options: ['Phòng A101', 'Phòng A102', 'Giảng đường A', 'Giảng đường B'] },
        { id: 'duration', label: 'Thời gian sử dụng', type: 'text', required: true, placeholder: 'VD: 8:00 - 12:00' },
        { id: 'purpose', label: 'Mục đích sử dụng', type: 'textarea', required: true, placeholder: 'Mô tả chi tiết mục đích' }
      ],
      documentTemplate: 'room-registration-template'
    },
    {
      id: 'course-registration',
      title: 'Đơn xin đăng ký vào lớp đầy',
      description: 'SV toàn Đại học xin đăng ký vào lớp đầy các học phần do Khoa Toán-Tin phụ trách (đặt c...',
      fullDescription: 'Sinh viên toàn Đại học xin đăng ký vào lớp đầy các học phần do Khoa Toán-Tin phụ trách (đặc biệt các lớp thực hành).',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'class', label: 'Lớp', type: 'text', required: true, placeholder: 'Nhập lớp hiện tại' },
        { id: 'subjectCode', label: 'Mã học phần', type: 'text', required: true, placeholder: 'Nhập mã học phần' },
        { id: 'subjectName', label: 'Tên học phần', type: 'text', required: true, placeholder: 'Nhập tên học phần' },
        { id: 'reason', label: 'Lý do đăng ký', type: 'textarea', required: true, placeholder: 'Nêu rõ lý do cần đăng ký' }
      ],
      documentTemplate: 'course-registration-template'
    },
    {
      id: 'study-abroad',
      title: 'ĐƠN XIN ĐĂNG KÝ VÀO LỚP ĐẶC BIỆT',
      description: 'Dùng cho SV được cấp học bổng trao đổi sinh viên của ĐHBK Hà Nội',
      fullDescription: 'Đơn xin đăng ký vào lớp đặc biệt dành cho sinh viên được cấp học bổng trao đổi sinh viên của ĐHBK Hà Nội hoặc các chương trình học tập ở nước ngoài.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'faculty', label: 'Khoa', type: 'text', required: true, placeholder: 'Nhập tên khoa' },
        { id: 'program', label: 'Chương trình', type: 'select', required: true, options: ['Trao đổi sinh viên', 'Học bổng toàn phần', 'Học bổng một phần', 'Chương trình liên kết'] },
        { id: 'country', label: 'Quốc gia', type: 'text', required: true, placeholder: 'Nhập quốc gia' },
        { id: 'university', label: 'Trường đại học', type: 'text', required: true, placeholder: 'Nhập tên trường' },
        { id: 'duration', label: 'Thời gian', type: 'text', required: true, placeholder: 'VD: 1 học kỳ, 1 năm học' },
        { id: 'purpose', label: 'Mục đích', type: 'textarea', required: true, placeholder: 'Mô tả mục đích học tập' }
      ],
      documentTemplate: 'study-abroad-template'
    },
    {
      id: 'student-certificate',
      title: 'Giấy chứng nhận được học bổng khuyến khích học tập',
      description: 'Giấy xác nhận là sinh viên của đại học, áp dụng cho các sinh viên đang học tập tại đại...',
      fullDescription: 'Giấy chứng nhận sinh viên được học bổng khuyến khích học tập dành cho sinh viên có thành tích học tập tốt.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'faculty', label: 'Khoa', type: 'text', required: true, placeholder: 'Nhập tên khoa' },
        { id: 'major', label: 'Ngành học', type: 'text', required: true, placeholder: 'Nhập tên ngành' },
        { id: 'gpa', label: 'GPA', type: 'text', required: true, placeholder: 'Nhập điểm GPA' },
        { id: 'semester', label: 'Học kỳ', type: 'text', required: true, placeholder: 'VD: HK1 2023-2024' },
        { id: 'purpose', label: 'Mục đích sử dụng', type: 'textarea', required: true, placeholder: 'Nêu rõ mục đích sử dụng giấy chứng nhận' }
      ],
      documentTemplate: 'scholarship-certificate-template'
    },
    {
      id: 'bilingual-student',
      title: 'Giấy chứng nhận sinh viên',
      description: 'Giấy xác nhận là sinh viên của đại học, áp dụng cho các sinh viên đang học tập tại đại...',
      fullDescription: 'Giấy chứng nhận sinh viên dành cho các mục đích như xin việc làm thêm, vay vốn ngân hàng, các thủ tục hành chính khác.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'birthDate', label: 'Ngày sinh', type: 'date', required: true },
        { id: 'birthPlace', label: 'Nơi sinh', type: 'text', required: true, placeholder: 'Nhập nơi sinh' },
        { id: 'faculty', label: 'Khoa', type: 'text', required: true, placeholder: 'Nhập tên khoa' },
        { id: 'major', label: 'Ngành học', type: 'text', required: true, placeholder: 'Nhập tên ngành' },
        { id: 'course', label: 'Khóa học', type: 'text', required: true, placeholder: 'VD: K67' },
        { id: 'purpose', label: 'Mục đích sử dụng', type: 'textarea', required: true, placeholder: 'Nêu rõ mục đích sử dụng' }
      ],
      documentTemplate: 'student-certificate-template'
    },
    {
      id: 'bilingual-student-intro',
      title: 'Giấy chứng nhận sinh viên song ngữ',
      description: 'Trong quá trình học tập, sinh viên có nhu cầu sử dụng Giấy giới thiệu SV phục vụ cho việc...',
      fullDescription: 'Giấy chứng nhận sinh viên song ngữ (Việt-Anh) phục vụ cho các mục đích quốc tế như xin visa, học bổng, thực tập ở nước ngoài.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'englishName', label: 'Tên tiếng Anh', type: 'text', required: false, placeholder: 'Nhập tên tiếng Anh (nếu có)' },
        { id: 'birthDate', label: 'Ngày sinh', type: 'date', required: true },
        { id: 'birthPlace', label: 'Nơi sinh', type: 'text', required: true, placeholder: 'Nhập nơi sinh' },
        { id: 'faculty', label: 'Khoa', type: 'text', required: true, placeholder: 'Nhập tên khoa' },
        { id: 'major', label: 'Ngành học', type: 'text', required: true, placeholder: 'Nhập tên ngành' },
        { id: 'purpose', label: 'Mục đích sử dụng', type: 'textarea', required: true, placeholder: 'Nêu rõ mục đích sử dụng (tiếng Việt và tiếng Anh)' }
      ],
      documentTemplate: 'bilingual-certificate-template'
    },
    {
      id: 'student-intro',
      title: 'Giấy giới thiệu sinh viên',
      description: 'Trong quá trình học tập, sinh viên có nhu cầu sử dụng Giấy giới thiệu SV phục vụ cho việc...',
      fullDescription: 'Giấy giới thiệu sinh viên dành cho các hoạt động như thực tập, tham quan, nghiên cứu, khảo sát tại các cơ quan, doanh nghiệp.',
      fields: [
        { id: 'studentId', label: 'MSSV', type: 'text', required: true, placeholder: 'Nhập mã số sinh viên' },
        { id: 'fullName', label: 'Họ và tên', type: 'text', required: true, placeholder: 'Nhập họ và tên đầy đủ' },
        { id: 'faculty', label: 'Khoa', type: 'text', required: true, placeholder: 'Nhập tên khoa' },
        { id: 'major', label: 'Ngành học', type: 'text', required: true, placeholder: 'Nhập tên ngành' },
        { id: 'destination', label: 'Nơi đến', type: 'text', required: true, placeholder: 'Nhập tên cơ quan/doanh nghiệp' },
        { id: 'purpose', label: 'Mục đích', type: 'select', required: true, options: ['Thực tập', 'Tham quan', 'Nghiên cứu', 'Khảo sát', 'Khác'] },
        { id: 'duration', label: 'Thời gian', type: 'text', required: true, placeholder: 'VD: từ 01/01/2024 đến 31/01/2024' },
        { id: 'details', label: 'Chi tiết công việc', type: 'textarea', required: true, placeholder: 'Mô tả chi tiết công việc cần thực hiện' }
      ],
      documentTemplate: 'student-intro-template'
    }
  ]

  const handleFormSelect = (form: FormTemplate) => {
    setSelectedForm(form)
    setFormData({})
    setShowModal(true)
  }

  const handleFormSubmit = (data: Record<string, string>) => {
    setFormData(data)
    setShowModal(false)
    setShowPreview(true)
  }

  const handleSendForm = async () => {
    if (!selectedForm) return
    
    try {
      // Tạo nội dung email với thông tin form
      const emailContent = {
        formTitle: selectedForm.title,
        formData: formData,
        timestamp: new Date().toISOString()
      }

      // Gửi email đến admin (sẽ implement sau)
      console.log('Sending form to admin:', emailContent)
      
      // Hiển thị thông báo thành công
      alert('Đơn đã được gửi thành công! Bạn sẽ nhận được thông báo khi đơn được xử lý.')
      
      // Reset state
      setShowPreview(false)
      setSelectedForm(null)
      setFormData({})
    } catch (error) {
      console.error('Error sending form:', error)
      alert('Có lỗi xảy ra khi gửi đơn. Vui lòng thử lại!')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Biểu mẫu</h1>
      </div>
      
      {/* Grid các biểu mẫu */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {formTemplates.map((form) => (
          <FormCard
            key={form.id}
            form={form}
            onClick={() => handleFormSelect(form)}
          />
        ))}
      </div>

      {/* Modal điền form */}
      {showModal && selectedForm && (
        <FormModal
          form={selectedForm}
          onClose={() => {
            setShowModal(false)
            setSelectedForm(null)
          }}
          onSubmit={handleFormSubmit}
        />
      )}

      {/* Preview document */}
      {showPreview && selectedForm && (
        <DocumentPreview
          form={selectedForm}
          formData={formData}
          onClose={() => {
            setShowPreview(false)
            setSelectedForm(null)
          }}
          onSend={handleSendForm}
        />
      )}

      {/* Hướng dẫn sinh viên */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4 border-b border-red-500 pb-2">Hướng dẫn sinh viên</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-gray-800 mb-2">1. Hướng dẫn sử dụng Dịch vụ trực tuyến</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
              <li>Mỗi sinh viên của Trường được cấp 01 tài khoản với ID và Pass chính là MSSV.</li>
              <li>Sinh viên đăng nhập lần đầu rồi tự đổi Pass của riêng mình.</li>
              <li>Sinh viên điền yêu cầu vào biểu mẫu online.</li>
              <li>Hệ thống sẽ gửi email thông báo cho Sinh viên khi yêu cầu hoàn thành</li>
              <li>Sinh viên đem theo thẻ Sinh viên lên Văn phòng Trường để nhận</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">2. Các biểu mẫu giấy tờ hỗ trợ đăng kí online</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
              <li>Giấy Chứng nhận Sinh viên cấp Trường</li>
              <li>Giấy Giới thiệu cấp Trường</li>
              <li>In sao bảng điểm</li>
              <li>Giấy chứng nhận Tốt nghiệp</li>
              <li>Các mẫu đơn chung (chỉ áp dụng với đơn có xin dấu của Lãnh đạo Trường)</li>
              <li>Đơn xin chuyển điểm tương đương (SV phải nộp kèm bảng điểm)</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">3. Liên hệ để nhận giấy tờ tại Văn phòng Trường</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
              <li><strong>Cô Nguyễn Thị Hiền:</strong> Bảng điểm, Chứng nhận tốt nghiệp cho Sinh viên hệ Đại học</li>
              <li><strong>Cô Nguyễn Thanh Nguyệt:</strong> Bảng điểm, chứng nhận tốt nghiệp cho Học viên Cao học</li>
              <li><strong>Cô Đinh Thu Hương:</strong> Giấy xác nhận SV đã đ/ký qua hệ thống trực tuyến và Các giấy tờ khác (Vé xe bus, giấy đăng ký thuê nhà ở đơn vị tập thể, ...)</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">4. Thời gian làm việc tại Văn phòng Trường</h3>
            <div className="text-gray-600 space-y-2 ml-4">
              <p><strong>Nhận yêu cầu (Với các biểu mẫu không yêu cầu online):</strong> Ngày Thứ 3, thứ 5</p>
              <p className="ml-4">• Sáng từ 8h30 đến 12h00</p>
              <p className="ml-4">• Chiều từ 13h30 đến 16h30</p>
              <p><strong>Trả giấy tờ:</strong> Ngày thứ 3, thứ 5</p>
              <p className="ml-4">• Sáng từ 8h30 đến 12h00</p>
              <p className="ml-4">• Chiều từ 13h30 đến 16h30</p>
              <p><strong>Với các giấy tờ cần dấu Đại học:</strong> Sau khi nhận tại trường, Sinh viên tự đi lấy dấu tại phòng Hành chính tổng hợp nhà C1 - 114</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">5. Lưu ý</h3>
            <p className="text-gray-600 ml-4">
              Các loại giấy Xác nhận chế độ chính sách, giấy Xác nhận vay vốn, giấy Chứng nhận mất thẻ sinh viên, 
              sinh viên xuống làm việc trực tiếp tại phòng CTCT & CTSV - Nhà C1-104, để được giải quyết.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Forms
