import React, { useState } from 'react'
import { Button, message } from 'antd'
import { downloadDocument, type FormData } from '../../services/document-service'
import { sendEmailWithAttachment } from '../../services/emailjs-service'

interface DocumentPreviewProps {
  formData: any
  onBack: () => void
  onSubmit: () => void
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ formData, onBack, onSubmit }) => {
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      // Step 1: Generate and download document
      message.loading('Đang tạo và tải xuống tài liệu...', 0)
      const documentBlob = await downloadDocument(formData as FormData)
      message.destroy() // Clear loading message
      message.success('Tài liệu đã được tải xuống!')
      
      // Step 2: Send email with document to admin
      message.loading('Đang gửi email cho admin...', 0)
      const emailSent = await sendEmailWithAttachment({
        studentName: formData.studentName,
        studentId: formData.studentId,
        formType: getFormTitle(formData.formType),
        formData: formData,
        documentBlob: documentBlob
      })
      
      message.destroy() // Clear loading message
      
      if (emailSent) {
        message.success('Email đã được gửi cho admin thành công!')
        
        // Step 3: Create notification for student via API
        await createNotificationForStudent()
        
        message.success('Đơn đã được xử lý hoàn tất!')
      } else {
        message.warning('Tài liệu đã tải xuống nhưng có lỗi khi gửi email cho admin')
      }
      
      onSubmit()
    } catch (error) {
      message.destroy() // Clear any loading messages
      console.error('Lỗi khi xử lý đơn:', error)
      message.error('Có lỗi xảy ra khi xử lý đơn')
    } finally {
      setLoading(false)
    }
  }

  const createNotificationForStudent = async () => {
    try {
      const response = await fetch('http://localhost:8000/student-forms/notification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: formData.studentId,
          title: 'Đơn đã được gửi',
          message: `Đơn ${getFormTitle(formData.formType)} của bạn đã được gửi thành công cho Ban Giám hiệu.`,
          type: 'info'
        }),
      })
      
      if (response.ok) {
        console.log('Notification created successfully')
      }
    } catch (error) {
      console.error('Error creating notification:', error)
      // Don't throw error as this is not critical
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white border rounded-lg p-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mb-4">
            <p className="font-bold text-lg">ĐẠI HỌC BÁCH KHOA HÀ NỘI</p>
            <p className="font-bold text-lg">TRƯỜNG CÔNG NGHỆ THÔNG TIN</p>
            <p className="font-bold text-lg">VÀ TRUYỀN THÔNG</p>
          </div>
          
          <div className="mb-6">
            <p className="font-bold">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p>
            <p className="font-bold">Độc lập – Tự do – Hạnh phúc</p>
          </div>
          
          <div className="mb-8">
            <h2 className="text-xl font-bold">{getFormTitle(formData.formType)}</h2>
          </div>
        </div>

        {/* Content */}
        <div className="space-y-4 text-left">
          <p>Kính gửi: Ban Giám hiệu Trường Công nghệ Thông tin và Truyền thông</p>
          
          <div className="space-y-2">
            <p>Tôi là: <strong>{formData.studentName}</strong></p>
            <p>MSSV: <strong>{formData.studentId}</strong></p>
            <p>Lớp: <strong>{formData.class}</strong></p>
            <p>Khóa: <strong>{formData.course}</strong></p>
            <p>Email: <strong>{formData.email}</strong></p>
            {formData.phone && <p>Số điện thoại: <strong>{formData.phone}</strong></p>}
            {formData.address && <p>Địa chỉ: <strong>{formData.address}</strong></p>}
          </div>

          <p>{getFormContent(formData.formType)}</p>
          
          {formData.reason && <p>Lý do: <strong>{formData.reason}</strong></p>}
          {formData.purpose && <p>Mục đích sử dụng: <strong>{formData.purpose}</strong></p>}
          {formData.details && <p>Chi tiết: <strong>{formData.details}</strong></p>}

          <p>Tôi xin chân thành cảm ơn!</p>

          <div className="text-right mt-8">
            <p>Hà Nội, ngày {new Date().getDate()} tháng {new Date().getMonth() + 1} năm {new Date().getFullYear()}</p>
            <p className="font-bold mt-2">Sinh viên</p>
            <p className="mt-4">{formData.studentName}</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-center space-x-4">
        <Button onClick={onBack} size="large">
          Quay lại
        </Button>
        <Button 
          type="primary" 
          onClick={handleSubmit} 
          loading={loading}
          size="large"
        >
          Gửi yêu cầu
        </Button>
      </div>
    </div>
  )
}

const getFormTitle = (formType: string): string => {
  const titles: { [key: string]: string } = {
    'student-certificate': 'GIẤY XÁC NHẬN SINH VIÊN',
    'student-introduction': 'GIẤY GIỚI THIỆU SINH VIÊN', 
    'transcript-request': 'ĐƠN XIN CẤP BẢNG ĐIỂM',
    'graduation-certificate': 'ĐƠN XIN CẤP CHỨNG CHỈ TỐT NGHIỆP',
    'scholarship-application': 'ĐƠN XIN HỌC BỔNG',
    'dormitory-application': 'ĐƠN XIN ĐĂNG KÝ KÝ TÚC XÁ',
    'study-abroad-application': 'ĐƠN XIN ĐĂNG KÝ DU HỌC',
    'bus-pass-application': 'ĐƠN ĐĂNG KÝ VÉ XE BUÝT',
    'credit-transfer': 'ĐƠN XIN CHUYỂN ĐỔI TÍN CHỈ',
    'loan-certificate': 'GIẤY XÁC NHẬN VAY VỐN NGÂN HÀNG',
    'housing-registration': 'ĐƠN ĐĂNG KÝ NHÀ Ở PHÁP VÂN'
  }
  return titles[formType] || 'ĐƠN XIN'
}

const getFormContent = (formType: string): string => {
  const contents: { [key: string]: string } = {
    'student-certificate': 'Tôi viết đơn này đề nghị Nhà trường cấp giấy xác nhận sinh viên để phục vụ cho việc học tập và các thủ tục cần thiết.',
    'student-introduction': 'Tôi viết đơn này đề nghị Nhà trường cấp giấy giới thiệu sinh viên để thực hiện các hoạt động học tập và nghiên cứu.',
    'transcript-request': 'Tôi viết đơn này đề nghị Nhà trường cấp bảng điểm để phục vụ cho việc xin học bổng, chuyển trường hoặc các mục đích khác.',
    'graduation-certificate': 'Tôi viết đơn này đề nghị Nhà trường cấp chứng chỉ tốt nghiệp để phục vụ cho việc tìm kiếm việc làm và các thủ tục pháp lý.',
    'scholarship-application': 'Tôi viết đơn này đề nghị được xét cấp học bổng dựa trên kết quả học tập và hoàn cảnh gia đình.',
    'dormitory-application': 'Tôi viết đơn này đề nghị được đăng ký ở ký túc xá của trường trong thời gian học tập.',
    'study-abroad-application': 'Tôi viết đơn này đề nghị được tham gia chương trình trao đổi sinh viên hoặc du học.',
    'bus-pass-application': 'Tôi viết đơn này đề nghị được cấp vé xe buýt ưu đãi cho sinh viên.',
    'credit-transfer': 'Tôi viết đơn này đề nghị được chuyển đổi tín chỉ từ các môn học đã hoàn thành ở trường khác.',
    'loan-certificate': 'Tôi viết đơn này đề nghị Nhà trường cấp giấy xác nhận để thực hiện thủ tục vay vốn ngân hàng phục vụ học tập.',
    'housing-registration': 'Tôi viết đơn này đề nghị được đăng ký thuê nhà ở khu vực Pháp Vân dành cho sinh viên.'
  }
  return contents[formType] || 'Tôi viết đơn này đề nghị Nhà trường hỗ trợ.'
}

export default DocumentPreview