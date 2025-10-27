import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import emailjs from '@emailjs/browser';

interface Scholarship {
  id: number;
  title: string;
  type: string;
  slots: number;
  value_per_slot: number;
  sponsor: string;
  register_start_at: string;
  register_end_at: string;
  target_departments: string;
  target_courses: string;
  target_programs: string;
  contact_person: string;
  contact_info: string;
  document_url: string;
  description: string;
  note: string;
  created_at: string;
  updated_at: string;
}

interface ScholarshipModalProps {
  scholarship: Scholarship;
  applicationStatus: string | null;
  onClose: () => void;
  onApplicationSubmitted: () => void;
}

interface ApplicationFormData {
  // Thông tin cơ bản - phải match với API schema
  scholarship_id: number;
  student_id: number;  // Changed to integer ID
  
  // Thông tin ngân hàng
  bank_account_number: string;
  bank_name: string;
  phone_number: string;
  
  // Thông tin gia đình và địa chỉ
  family_status: string;
  address_country: string;
  address_city: string;
  address_ward: string;
  address_detail: string;
  family_description: string;
  
  // Thành tích và lý do
  achievement_special: string;
  achievement_activity: string;
  reason_apply: string;
  
  // Files đính kèm (tối đa 3 files)
  attachment_files: File[];
}

// Auto-calculated fields from backend (readonly)
interface AutoData {
  auto_cpa: number;
  auto_gpa: number;
  auto_drl_latest: number;
  auto_drl_average: number;
  auto_gpa_last_2_sem: number;
  auto_drl_last_2_sem: string;
  auto_total_credits: number;
}

const ScholarshipModal: React.FC<ScholarshipModalProps> = ({
  scholarship,
  applicationStatus,
  onClose,
  onApplicationSubmitted
}) => {
  const { userInfo } = useAuth();
  const [showApplicationForm, setShowApplicationForm] = useState(false);
  const [activeSection, setActiveSection] = useState(1);
  const [formData, setFormData] = useState<ApplicationFormData>({
    scholarship_id: scholarship.id,
    student_id: userInfo?.id || 0, // Lấy từ userInfo, integer ID
    bank_account_number: '',
    bank_name: '',
    phone_number: '',
    family_status: 'bình thường',
    address_country: 'Việt Nam',
    address_city: '',
    address_ward: '',
    address_detail: '',
    family_description: '',
    achievement_special: '',
    achievement_activity: '',
    reason_apply: '',
    attachment_files: []
  });

  // Auto-calculated data (readonly)
  const [autoData, setAutoData] = useState<AutoData>({
    auto_cpa: 0,
    auto_gpa: 0,
    auto_drl_latest: 0,
    auto_drl_average: 0,
    auto_gpa_last_2_sem: 0,
    auto_drl_last_2_sem: '0',
    auto_total_credits: 0
  });

  // Refs for scrolling
  const section1Ref = useRef<HTMLDivElement>(null);
  const section2Ref = useRef<HTMLDivElement>(null);
  const section3Ref = useRef<HTMLDivElement>(null);
  const section4Ref = useRef<HTMLDivElement>(null);

  // Load auto data từ API
  React.useEffect(() => {
    const loadAutoData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/scholarship-applications/auto-fields');
        if (response.ok) {
          const data = await response.json();
          setAutoData({
            auto_cpa: data.auto_cpa || 0,
            auto_gpa: data.auto_gpa || 0,
            auto_drl_latest: data.auto_drl_latest || 0,
            auto_drl_average: data.auto_drl_average || 0,
            auto_gpa_last_2_sem: data.auto_gpa_last_2_sem || 0,
            auto_drl_last_2_sem: data.auto_drl_last_2_sem || '0',
            auto_total_credits: data.auto_total_credits || 0
          });
        }
      } catch (error) {
        console.error('Error loading auto data:', error);
      }
    };

    loadAutoData();
  }, []); // Load once when component mounts

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  const scrollToSection = (sectionNumber: number) => {
    const refs = [section1Ref, section2Ref, section3Ref, section4Ref];
    refs[sectionNumber - 1]?.current?.scrollIntoView({ behavior: 'smooth' });
    setActiveSection(sectionNumber);
  };

  const handleInputChange = (field: keyof ApplicationFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    // Validate number of files
    if (files.length > 3) {
      alert('Chỉ được chọn tối đa 3 files!');
      return;
    }

    // Validate file types
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
    for (const file of files) {
      if (!allowedTypes.includes(file.type)) {
        alert(`File ${file.name} không được hỗ trợ. Chỉ hỗ trợ PNG, JPG, JPEG, PDF.`);
        return;
      }
      
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} quá lớn. Tối đa 10MB.`);
        return;
      }
    }

    setFormData(prev => ({
      ...prev,
      attachment_files: files
    }));
  };

  const removeFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      attachment_files: prev.attachment_files.filter((_, i) => i !== index)
    }));
  };

  const handleSave = async () => {
    try {
      // Create FormData to handle file uploads
      const formDataToSend = new FormData();
      
      // Add all form fields including student_id
      Object.entries(formData).forEach(([key, value]) => {
        if (key !== 'attachment_files' && value !== undefined && value !== null) {
          formDataToSend.append(key, value.toString());
        }
      });
      
      // Add auto fields
      Object.entries(autoData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formDataToSend.append(key, value.toString());
        }
      });
      
      // Add files
      formData.attachment_files.forEach((file) => {
        formDataToSend.append('files', file);
      });

      const response = await fetch('http://localhost:8000/api/scholarship-applications/create-with-files', {
        method: 'POST',
        body: formDataToSend // Don't set Content-Type, let browser handle it for FormData
      });

      if (response.ok) {
        const result = await response.json();
        alert('Lưu thông tin thành công!');
        console.log('Application created:', result);
      } else {
        const error = await response.json();
        alert(`Lỗi khi lưu thông tin: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving application:', error);
      alert('Có lỗi xảy ra khi lưu');
    }
  };

  const handleSubmit = async () => {
    try {
      // Validate required fields
      if (!formData.bank_account_number || !formData.bank_name || !formData.phone_number) {
        alert('Vui lòng điền đầy đủ thông tin bắt buộc!');
        return;
      }

      // Create FormData to handle file uploads
      const formDataToSend = new FormData();
      
      // Add all form fields including student_id  
      Object.entries(formData).forEach(([key, value]) => {
        if (key !== 'attachment_files' && value !== undefined && value !== null) {
          formDataToSend.append(key, value.toString());
        }
      });
      
      // Add auto fields
      Object.entries(autoData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formDataToSend.append(key, value.toString());
        }
      });
      
      // Add files
      formData.attachment_files.forEach((file) => {
        formDataToSend.append('files', file);
      });

      const response = await fetch('http://localhost:8000/api/scholarship-applications/create-with-files', {
        method: 'POST',
        body: formDataToSend
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create application');
      }

      const result = await response.json();

      // 2. Gửi email cho admin bằng EmailJS  
      const emailData = {
        scholarship_title: scholarship.title,
        student_name: 'Sinh viên', // Có thể lấy từ student data
        student_phone: formData.phone_number,
        bank_account: formData.bank_account_number,
        bank_name: formData.bank_name,
        application_reason: formData.reason_apply,
        submit_date: new Date().toLocaleDateString('vi-VN'),
        to_email: 'admin@university.edu.vn'
      };

      try {
        await emailjs.send(
          'service_your_service_id', 
          'template_scholarship_application',
          emailData,
          'your_public_key'
        );
        console.log('Email sent successfully');
      } catch (emailError) {
        console.error('Failed to send email:', emailError);
        // Don't fail the whole process if email fails
      }

      alert('Nộp hồ sơ thành công! Thông tin đã được gửi đến ban quản lý.');
      onApplicationSubmitted();
      onClose();

    } catch (error) {
      console.error('Error submitting application:', error);
      alert('Có lỗi xảy ra khi nộp hồ sơ');
    }
  };

  return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg w-full max-w-7xl max-h-[95vh] overflow-hidden flex">
          {/* Main Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-center mb-6 pb-4 border-b-2 border-red-200">
                <h2 className="text-xl font-bold text-red-600">
                  Thông tin xét duyệt học bổng
                </h2>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ✕
                </button>
              </div>

              {/* Section 1: Thông tin chung */}
              <div ref={section1Ref} className="mb-8">
                <div 
                  className="flex items-center justify-between mb-4 p-4 bg-blue-50 rounded-lg cursor-pointer hover:bg-blue-100"
                  onClick={() => scrollToSection(1)}
                >
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold mr-3">
                      1
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Thông tin chung</h3>
                  </div>
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  {/* Tên học bổng */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tên học bổng <span className="text-red-500">*</span>
                    </label>
                    <div className="text-lg font-medium text-blue-600">
                      {scholarship.title}
                    </div>
                  </div>

                  {/* Row 1: Loại học bổng, Số lượng, Giá trị, Đối tác */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Loại học bổng
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {scholarship.type}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Số lượng học bổng
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-center">
                        {scholarship.slots}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Giá trị học bổng/suất
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-center">
                        {scholarship.value_per_slot.toLocaleString('vi-VN')}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Đối tác cấp học bổng
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {scholarship.sponsor}
                      </div>
                    </div>
                  </div>

                  {/* Row 2: Ngày đăng ký */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Ngày bắt đầu đăng ký <span className="text-red-500">*</span>
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {new Date(scholarship.register_start_at).toLocaleDateString('vi-VN')} {new Date(scholarship.register_start_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Ngày kết thúc đăng ký <span className="text-red-500">*</span>
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {new Date(scholarship.register_end_at).toLocaleDateString('vi-VN')} {new Date(scholarship.register_end_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}
                      </div>
                    </div>
                  </div>

                  {/* Row 3: Đối tượng sinh viên */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Dành cho sinh viên các đơn vị
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg min-h-[80px]">
                        {scholarship.target_departments}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Dành cho sinh viên các khóa
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {scholarship.target_courses}
                      </div>
                    </div>
                  </div>

                  {/* Row 4: Dành cho sinh viên các hệ */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dành cho sinh viên các hệ <span className="text-red-500">*</span>
                    </label>
                    <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                      {scholarship.target_programs || 'Cử nhân tích hợp, Cử nhân kỹ thuật, Chương trình tiên tiến - Tiếng Việt, Hệ đào tạo quốc tế, Chương trình tài năng, Chương trình tiên tiến, Cử nhân Khoa học, CNTT Việt - Pháp, Cử nhân, Việt-Nhật'}
                    </div>
                  </div>

                  {/* Row 5: Liên hệ */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Cán bộ phụ trách
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {scholarship.contact_person}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Thông tin liên hệ
                      </label>
                      <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg">
                        {scholarship.contact_info}
                      </div>
                    </div>
                  </div>

                  {/* Tài liệu */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tài liệu
                    </label>
                    <div className="border border-gray-300 rounded-lg p-3">
                      {scholarship.document_url ? (
                        <a
                          href={scholarship.document_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center"
                        >
                          📄 {scholarship.document_url.split('/').pop() || 'mau_don_don_dang_ky_xet_hb_tai_tro.doc'}
                        </a>
                      ) : (
                        <span className="text-gray-400">Không có tài liệu đính kèm</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 2: Thông tin chi tiết */}
              <div ref={section2Ref} className="mb-8">
                <div 
                  className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => scrollToSection(2)}
                >
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                      2
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Thông tin chi tiết</h3>
                  </div>
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-line text-gray-700 leading-relaxed">
                      {scholarship.description || 'Mô tả chi tiết về học bổng sẽ được cập nhật sau.'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 3: Thông tin đăng ký học bổng */}
              <div ref={section3Ref} className="mb-8">
                <div 
                  className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => scrollToSection(3)}
                >
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                      3
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Thông tin đăng ký học bổng</h3>
                  </div>
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Bạn đăng ký học bổng nào <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={scholarship.title}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Đối tượng nhận học bổng <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={` ${userInfo?.student_name }`}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        STK nhận học bổng nếu đạt <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.bank_account_number}
                        onChange={(e) => handleInputChange('bank_account_number', e.target.value)}
                        placeholder="Nhập số tài khoản chính chủ, lưu ..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tại ngân hàng nào (VD: BIDV, Vietinbank, ...) <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.bank_name}
                        onChange={(e) => handleInputChange('bank_name', e.target.value)}
                        placeholder="Nhập tên ngân hàng"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Số điện thoại hiện tại <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        value={formData.phone_number}
                        onChange={(e) => handleInputChange('phone_number', e.target.value)}
                        placeholder="Nhập số điện thoại"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm CPA <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_cpa.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm GPA <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_gpa.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm rèn luyện kỳ gần nhất <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_drl_latest.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm rèn luyện TB tích lũy <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_drl_average.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm TB 2 HK gần nhất <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_gpa_last_2_sem.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Điểm rèn luyện 2 kỳ gần nhất <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_drl_last_2_sem}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tổng số tín chỉ tích lũy <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={autoData.auto_total_credits.toString()}
                        readOnly
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Hoàn cảnh gia đình <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.family_status}
                      onChange={(e) => handleInputChange('family_status', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="bình thường">Hộ bình thường</option>
                      <option value="khó khăn">Hộ khó khăn</option>
                      <option value="cận nghèo">Hộ cận nghèo</option>
                      <option value="nghèo">Hộ nghèo</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Quốc gia
                      </label>
                      <input
                        type="text"
                        value={formData.address_country}
                        onChange={(e) => handleInputChange('address_country', e.target.value)}
                        
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tỉnh/Thành phố
                      </label>
                      <input
                        type="text"
                        value={formData.address_city}
                        onChange={(e) => handleInputChange('address_city', e.target.value)}
                        
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phường/Xã
                      </label>
                      <input
                        type="text"
                        value={formData.address_ward}
                        onChange={(e) => handleInputChange('address_ward', e.target.value)}
                        
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Địa chỉ chi tiết
                      </label>
                      <input
                        type="text"
                        value={formData.address_detail}
                        onChange={(e) => handleInputChange('address_detail', e.target.value)}
                        
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Mô tả ngắn gọn hoàn cảnh gia đình
                    </label>
                    <textarea
                      value={formData.family_description}
                      onChange={(e) => handleInputChange('family_description', e.target.value)}
                      placeholder="Nhập không quá 300 từ"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Thành tích học tập, NCKH MST được khen thưởng trong thời gian học tập tại 
                        Đại học Bách khoa Hà Nội (Yêu cầu tải minh chứng lên)
                      </label>
                      <textarea
                        value={formData.achievement_special}
                        onChange={(e) => handleInputChange('achievement_special', e.target.value)}
                        placeholder="Thành tích học tập của bạn"
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Thành tích hoạt động phong trào Đoàn - Hội được khen thưởng trong thời 
                        gian học tập tại Đại học Bách khoa Hà Nội (tải minh chứng lên)
                      </label>
                      <textarea
                        value={formData.achievement_activity}
                        onChange={(e) => handleInputChange('achievement_activity', e.target.value)}
                        placeholder="Thành tích hoạt động của bạn"
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Lý do đăng ký học bổng <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={formData.reason_apply}
                      onChange={(e) => handleInputChange('reason_apply', e.target.value)}
                      placeholder="Nhập lý do của bạn"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              </div>

              {/* Section 4: Nộp hồ sơ đính kèm */}
              <div ref={section4Ref} className="mb-8">
                <div 
                  className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => scrollToSection(4)}
                >
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                      4
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Nộp hồ sơ đính kèm</h3>
                  </div>
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <p className="text-sm text-gray-600 mb-4">
                    <strong>Sinh viên tải các hồ sơ đính kèm:</strong><br />
                    <span className="text-red-600">Chú ý: Chỉ có thể tải lên file định (.png, .jpg, .jpeg) hoặc PDF (.pdf)</span>
                  </p>

                  <div className="space-y-4">
                    {/* File upload area */}
                    <div className="border-2 border-dashed border-red-300 rounded-lg p-6 text-center">
                      <input
                        type="file"
                        accept=".png,.jpg,.jpeg,.pdf"
                        multiple
                        onChange={handleFileChange}
                        className="hidden"
                        id="files-upload"
                      />
                      <label
                        htmlFor="files-upload"
                        className="cursor-pointer text-red-600 hover:text-red-800"
                      >
                        <div className="flex flex-col items-center">
                          <span className="text-3xl mb-2">📁</span>
                          <span className="text-sm font-medium">Tải file lên (tối đa 3 files)</span>
                          <span className="text-xs text-gray-500 mt-1">
                            Chỉ hỗ trợ file: PNG, JPG, JPEG, PDF
                          </span>
                        </div>
                      </label>
                    </div>

                    {/* Display uploaded files */}
                    {formData.attachment_files.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-gray-700">Files đã chọn:</h4>
                        {formData.attachment_files.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                            <div className="flex items-center">
                              <span className="text-sm text-gray-600 mr-2">📄</span>
                              <span className="text-sm text-gray-800">{file.name}</span>
                              <span className="text-xs text-gray-500 ml-2">
                                ({(file.size / 1024 / 1024).toFixed(2)} MB)
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeFile(index)}
                              className="text-red-500 hover:text-red-700 text-sm"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="w-80 bg-red-50 border-l-2 border-red-200 p-6">
            <div className="mb-8">
              <h3 className="text-lg font-bold text-red-600 mb-6">Mục lục</h3>
              
              <div className="space-y-2">
                <div
                  onClick={() => scrollToSection(1)}
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                    activeSection === 1 ? 'bg-blue-500 text-white' : 'text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <span className="font-medium">1. Thông tin chung</span>
                </div>
                <div
                  onClick={() => scrollToSection(2)}
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                    activeSection === 2 ? 'bg-blue-500 text-white' : 'text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <span className="font-medium">2. Thông tin chi tiết</span>
                </div>
                <div
                  onClick={() => scrollToSection(3)}
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                    activeSection === 3 ? 'bg-blue-500 text-white' : 'text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <span className="font-medium">3. Thông tin đăng ký học bổng</span>
                </div>
                <div
                  onClick={() => scrollToSection(4)}
                  className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                    activeSection === 4 ? 'bg-blue-500 text-white' : 'text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <span className="font-medium">4. Nộp hồ sơ đính kèm</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={handleSubmit}
                className="w-full bg-red-600 text-white py-4 px-6 rounded-full hover:bg-red-700 font-bold text-lg shadow-lg transition-all"
              >
                Nộp hồ sơ
              </button>
              
            </div>
          </div>
        </div>
      </div>
    );
  }

    

export default ScholarshipModal;