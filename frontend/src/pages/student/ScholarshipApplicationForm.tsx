import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
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
}

interface ApplicationFormData {
  bank_account_number: string;
  bank_name: string;
  phone_number: string;
  family_status: 'Bình thường' | 'Khó khăn' | 'Cận nghèo' | 'Nghèo';
  address_country: string;
  address_city: string;
  address_ward: string;
  address_detail: string;
  family_description: string;
  achievement_special: string;
  achievement_activity: string;
  reason_apply: string;
  attachment_url: string;
}

const ScholarshipApplicationForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { userInfo } = useAuth();
  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(1);
  
  // Refs for sections
  const section1Ref = useRef<HTMLDivElement>(null);
  const section2Ref = useRef<HTMLDivElement>(null);
  const section3Ref = useRef<HTMLDivElement>(null);
  const section4Ref = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState<ApplicationFormData>({
    bank_account_number: '',
    bank_name: '',
    phone_number: '',
    family_status: 'Bình thường',
    address_country: 'Việt Nam',
    address_city: '',
    address_ward: '',
    address_detail: '',
    family_description: '',
    achievement_special: '',
    achievement_activity: '',
    reason_apply: '',
    attachment_url: ''
  });

  // Auto-filled data from student profile
  const [autoData, setAutoData] = useState({
    auto_cpa: 0,
    auto_gpa: 0,
    auto_drl_latest: 0,
    auto_drl_average: 0,
    auto_gpa_last_2_sem: 0,
    auto_drl_last_2_sem: '',
    auto_total_credits: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch scholarship details
        const response = await fetch(`http://localhost:8000/api/scholarships/${id}`);
        if (response.ok) {
          const scholarshipData = await response.json();
          setScholarship(scholarshipData);
        }

        // Fetch auto-filled data
        const autoResponse = await fetch('http://localhost:8000/api/scholarship-applications/auto-fields');
        if (autoResponse.ok) {
          const autoFieldsData = await autoResponse.json();
          setAutoData(autoFieldsData);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchData();
    }
  }, [id]);

  // Scroll to section
  const scrollToSection = (sectionNumber: number) => {
    setActiveSection(sectionNumber);
    const refs = [null, section1Ref, section2Ref, section3Ref, section4Ref];
    const targetRef = refs[sectionNumber];
    if (targetRef?.current) {
      targetRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Handle form input change
  const handleInputChange = (field: keyof ApplicationFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, field: string) => {
    const file = event.target.files?.[0];
    if (file) {
      // Here you would implement actual file upload logic
      console.log(`Uploading ${field}:`, file);
      // For now, just store filename
      handleInputChange(field as keyof ApplicationFormData, file.name);
    }
  };

  // Save draft
  const handleSave = async () => {
    try {
      const applicationData = {
        scholarship_id: parseInt(id!),
        student_id: userInfo?.student_id || '20225818', // Fallback to student thực tế if no user info
        ...formData,
        ...autoData
      };

      const response = await fetch('http://localhost:8000/api/scholarship-applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(applicationData)
      });

      if (response.ok) {
        alert('Đã lưu thông tin thành công!');
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      console.error('Error saving:', error);
      alert('Có lỗi khi lưu thông tin!');
    }
  };

  // Submit application
  const handleSubmit = async () => {
    try {
      // First save the application
      await handleSave();

      // Send email to admin using EmailJS
      const emailData = {
        scholarship_name: scholarship?.title,
        student_name: 'Tên sinh viên', // Get from user context
        phone_number: formData.phone_number,
        bank_account: formData.bank_account_number,
        bank_name: formData.bank_name,
        reason_apply: formData.reason_apply,
        to_email: 'admin@university.edu.vn' // Admin email
      };

      await emailjs.send(
        'service_id', // Replace with your EmailJS service ID
        'template_id', // Replace with your EmailJS template ID
        emailData,
        'public_key' // Replace with your EmailJS public key
      );

      alert('Đã nộp hồ sơ thành công! Admin sẽ xem xét và phản hồi sớm nhất.');
      navigate('/student/scholarships');
    } catch (error) {
      console.error('Error submitting:', error);
      alert('Có lỗi khi nộp hồ sơ!');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Đang tải thông tin học bổng...</div>
      </div>
    );
  }

  if (!scholarship) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-red-600">Không tìm thấy thông tin học bổng!</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-red-600 text-white p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl font-bold">Thông tin xét duyệt học bổng</h1>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Main Content */}
          <div className="flex-1 bg-white rounded-lg shadow p-6">
            {/* Section 1: Thông tin chung */}
            <div ref={section1Ref} className="mb-8">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                  1
                </div>
                <h2 className="text-lg font-semibold">Thông tin chung</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tên học bổng *</label>
                  <input
                    type="text"
                    value={scholarship.title}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Loại học bổng</label>
                  <input
                    type="text"
                    value={scholarship.type}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Số lượng học bổng</label>
                  <input
                    type="text"
                    value={scholarship.slots.toString()}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Giá trị học bổng/suất</label>
                  <input
                    type="text"
                    value={scholarship.value_per_slot.toLocaleString('vi-VN') + ' VND'}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Đối tác cấp học bổng</label>
                  <input
                    type="text"
                    value={scholarship.sponsor}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ngày bắt đầu đăng ký *</label>
                  <input
                    type="datetime-local"
                    value={scholarship.register_start_at.slice(0, 16)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ngày kết thúc đăng ký *</label>
                  <input
                    type="datetime-local"
                    value={scholarship.register_end_at.slice(0, 16)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dành cho sinh viên các đơn vị</label>
                  <textarea
                    value={scholarship.target_departments}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                    rows={2}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dành cho sinh viên các khóa</label>
                  <input
                    type="text"
                    value={scholarship.target_courses}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dành cho sinh viên các hệ *</label>
                  <textarea
                    value={scholarship.target_programs}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                    rows={2}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cán bộ phụ trách</label>
                  <input
                    type="text"
                    value={scholarship.contact_person}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Thông tin liên hệ</label>
                  <input
                    type="text"
                    value={scholarship.contact_info}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Tài liệu</label>
                <div className="text-blue-600 underline">
                  <a href={scholarship.document_url} target="_blank" rel="noopener noreferrer">
                    {scholarship.document_url ? 'Xem tài liệu' : 'Không có tài liệu'}
                  </a>
                </div>
              </div>
            </div>

            {/* Section 2: Thông tin chi tiết */}
            <div ref={section2Ref} className="mb-8">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                  2
                </div>
                <h2 className="text-lg font-semibold">Thông tin chi tiết</h2>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <div dangerouslySetInnerHTML={{ __html: scholarship.description }} />
              </div>
            </div>

            {/* Section 3: Thông tin đăng ký học bổng */}
            <div ref={section3Ref} className="mb-8">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                  3
                </div>
                <h2 className="text-lg font-semibold">Thông tin đăng ký học bổng</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bạn đăng ký học bổng nào *</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  >
                    <option>Học bổng doanh nghiệp</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Đối tượng nhận học bổng *</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  >
                    <option>Khác</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">STK nhận học bổng nếu đạt *</label>
                  <input
                    type="text"
                    value={formData.bank_account_number}
                    onChange={(e) => handleInputChange('bank_account_number', e.target.value)}
                    placeholder="Nhập số tài khoản chính chủ, lưu ý..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tại ngân hàng nào (VD: BIDV, Vietinbank, ...)</label>
                  <input
                    type="text"
                    value={formData.bank_name}
                    onChange={(e) => handleInputChange('bank_name', e.target.value)}
                    placeholder="Nhập tên ngân hàng"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại hiện tại *</label>
                  <input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => handleInputChange('phone_number', e.target.value)}
                    placeholder="Nhập số điện thoại"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm CPA *</label>
                  <input
                    type="text"
                    value={autoData.auto_cpa.toFixed(2)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm GPA *</label>
                  <input
                    type="text"
                    value={autoData.auto_gpa.toFixed(2)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm rèn luyện kỳ gần nhất *</label>
                  <input
                    type="text"
                    value={autoData.auto_drl_latest.toString()}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm rèn luyện TB tích lũy *</label>
                  <input
                    type="text"
                    value={autoData.auto_drl_average.toFixed(2)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm TB 2 HK gần nhất *</label>
                  <input
                    type="text"
                    value={autoData.auto_gpa_last_2_sem.toFixed(2)}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm rèn luyện 2 kỳ gần nhất *</label>
                  <input
                    type="text"
                    value={autoData.auto_drl_last_2_sem}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tổng số tín chỉ tích lũy *</label>
                  <input
                    type="text"
                    value={autoData.auto_total_credits.toString()}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Hoàn cảnh gia đình *</label>
                <select
                  value={formData.family_status}
                  onChange={(e) => handleInputChange('family_status', e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                >
                  <option value="Bình thường">Hộ bình thường</option>
                  <option value="Khó khăn">Khó khăn</option>
                  <option value="Cận nghèo">Cận nghèo</option>
                  <option value="Nghèo">Nghèo</option>
                </select>
              </div>

              {/* Address fields */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <select
                    value={formData.address_country}
                    onChange={(e) => handleInputChange('address_country', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  >
                    <option>Việt Nam</option>
                  </select>
                </div>

                <div>
                  <select
                    value={formData.address_city}
                    onChange={(e) => handleInputChange('address_city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  >
                    <option>Thủ đô Hà Nội</option>
                  </select>
                </div>

                <div>
                  <select
                    value={formData.address_ward}
                    onChange={(e) => handleInputChange('address_ward', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  >
                    <option>Phường Phúc Lợi</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <input
                  type="text"
                  value={formData.address_detail}
                  onChange={(e) => handleInputChange('address_detail', e.target.value)}
                  placeholder="số 6, ngách 201/19, tổ 5, Phúc Lợi, Long Biên, Hà Nội"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả ngắn gọn hoàn cảnh gia đình</label>
                <textarea
                  value={formData.family_description}
                  onChange={(e) => handleInputChange('family_description', e.target.value)}
                  placeholder="Nhập không quá 300 từ"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Thành tích học tập, NCKDST được khen thưởng trong thời gian học tập tại Đại học Bách khoa Hà Nội (Yêu cầu tải minh chứng lên)
                  </label>
                  <textarea
                    value={formData.achievement_special}
                    onChange={(e) => handleInputChange('achievement_special', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Thành tích hoạt động phong trào Đoàn – Hội được khen thưởng trong thời gian học tập tại Đại học Bách khoa Hà Nội (tải minh chứng lên)
                  </label>
                  <textarea
                    value={formData.achievement_activity}
                    onChange={(e) => handleInputChange('achievement_activity', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
                  />
                </div>
              </div>
            </div>

            {/* Section 4: Nộp hồ sơ đính kèm */}
            <div ref={section4Ref} className="mb-8">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                  4
                </div>
                <h2 className="text-lg font-semibold">Nộp hồ sơ đính kèm</h2>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                <strong>Sinh viên tải các hồ sơ đính kèm:</strong><br />
                Chú ý: Chỉ có thể tải lên file ảnh (.png, .jpg, .jpeg) hoặc PDF (.pdf)
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Minh chứng hoàn cảnh khó khăn của gia đình có xác nhận của địa phương (nếu có)
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                    <input
                      type="file"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={(e) => handleFileUpload(e, 'family_proof')}
                      className="hidden"
                      id="family_proof"
                    />
                    <label htmlFor="family_proof" className="cursor-pointer flex flex-col items-center">
                      <div className="text-red-600 mb-2">⬆</div>
                      <span className="text-sm text-red-600">Tải file lên</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bài viết ngắn giới thiệu bản thân, năng lực học tập, mong muốn cá nhân trong tương lai
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                    <input
                      type="file"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={(e) => handleFileUpload(e, 'personal_essay')}
                      className="hidden"
                      id="personal_essay"
                    />
                    <label htmlFor="personal_essay" className="cursor-pointer flex flex-col items-center">
                      <div className="text-red-600 mb-2">⬆</div>
                      <span className="text-sm text-red-600">Tải file lên</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Các giấy khen (nếu có)
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                    <input
                      type="file"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={(e) => handleFileUpload(e, 'awards')}
                      className="hidden"
                      id="awards"
                    />
                    <label htmlFor="awards" className="cursor-pointer flex flex-col items-center">
                      <div className="text-red-600 mb-2">⬆</div>
                      <span className="text-sm text-red-600">Tải file lên</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Đơn xin học bổng (theo mẫu đính kèm thông báo)
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                    <input
                      type="file"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={(e) => handleFileUpload(e, 'application_form')}
                      className="hidden"
                      id="application_form"
                    />
                    <label htmlFor="application_form" className="cursor-pointer flex flex-col items-center">
                      <div className="text-red-600 mb-2">⬆</div>
                      <span className="text-sm text-red-600">Tải file lên</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-4 mt-8">
              <button
                onClick={handleSave}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
              >
                Lưu
              </button>
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:ring-2 focus:ring-red-500"
              >
                Nộp hồ sơ
              </button>
            </div>
          </div>

          {/* Sidebar Navigation */}
          <div className="w-80">
            <div className="bg-white rounded-lg shadow p-4 sticky top-6">
              <h3 className="font-semibold text-lg mb-4 text-red-600">Mục lục</h3>
              
              <div className="space-y-2">
                <button
                  onClick={() => scrollToSection(1)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeSection === 1 ? 'bg-red-100 text-red-700' : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  1. Thông tin chung
                </button>
                
                <button
                  onClick={() => scrollToSection(2)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeSection === 2 ? 'bg-red-100 text-red-700' : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  2. Thông tin chi tiết
                </button>
                
                <button
                  onClick={() => scrollToSection(3)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeSection === 3 ? 'bg-red-100 text-red-700' : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  3. Thông tin đăng ký học bổng
                </button>
                
                <button
                  onClick={() => scrollToSection(4)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    activeSection === 4 ? 'bg-red-100 text-red-700' : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  4. Nộp hồ sơ đính kèm
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScholarshipApplicationForm;