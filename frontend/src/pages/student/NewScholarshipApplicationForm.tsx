import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import emailjs from '@emailjs/browser';
import { sendFormEmail } from '../../services/emailjs-service';

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

interface AutoData {
  auto_cpa: number;
  auto_gpa: number;
  auto_drl_latest: number;
  auto_drl_average: number;
  auto_gpa_last_2_sem: number;
  auto_drl_last_2_sem: string;
  auto_total_credits: number;
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
  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [autoData, setAutoData] = useState<AutoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(1);

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

  useEffect(() => {
    if (id) {
      fetchScholarship();
      fetchAutoData();
    }
  }, [id]);

  const fetchScholarship = async () => {
    try {
      const response = await fetch(`/api/scholarships/${id}`);
      if (response.ok) {
        const data = await response.json();
        setScholarship(data);
      }
    } catch (error) {
      console.error('Error fetching scholarship:', error);
    }
  };

  const fetchAutoData = async () => {
    try {
      const response = await fetch('/api/scholarship-applications/auto-data');
      if (response.ok) {
        const data = await response.json();
        setAutoData(data);
      }
    } catch (error) {
      console.error('Error fetching auto data:', error);
    } finally {
      setLoading(false);
    }
  };

  const scrollToSection = (sectionNumber: number) => {
    setActiveSection(sectionNumber);
    const element = document.getElementById(`section-${sectionNumber}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleSave = async () => {
    try {
      const applicationData = {
        scholarship_id: parseInt(id!),
        ...formData,
        status: 'Chờ duyệt'
      };

      const response = await fetch('/api/scholarship-applications/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(applicationData),
      });

      if (response.ok) {
        alert('Đã lưu thông tin thành công!');
        return true;
      } else {
        alert('Có lỗi khi lưu thông tin!');
        return false;
      }
    } catch (error) {
      console.error('Error saving:', error);
      alert('Có lỗi khi lưu thông tin!');
      return false;
    }
  };

  const handleSubmit = async () => {
    try {
      // First save the application
      const saveSuccess = await handleSave();
      if (!saveSuccess) return;

      // Send email using existing EmailJS service
      const emailData = {
        studentName: 'Tên sinh viên', // Get from context/auth
        studentId: 'SV123456', // Get from context/auth
        studentEmail: 'student@email.com', // Get from context/auth
        formType: `Đăng ký học bổng: ${scholarship?.title}`,
        formContent: `
          Học bổng: ${scholarship?.title}
          Loại: ${scholarship?.type}
          Số điện thoại: ${formData.phone_number}
          Tài khoản ngân hàng: ${formData.bank_account_number} - ${formData.bank_name}
          Tình trạng gia đình: ${formData.family_status}
          Địa chỉ: ${formData.address_detail}, ${formData.address_ward}, ${formData.address_city}, ${formData.address_country}
          Lý do đăng ký: ${formData.reason_apply}
          
          Thành tích đặc biệt: ${formData.achievement_special}
          Hoạt động phong trào: ${formData.achievement_activity}
          Mô tả gia đình: ${formData.family_description}
        `,
        documentContent: formData.attachment_url || 'Không có tài liệu đính kèm'
      };

      const emailSuccess = await sendFormEmail(emailData);
      
      if (emailSuccess) {
        alert('Đã nộp hồ sơ thành công! Admin sẽ xem xét và phản hồi sớm nhất.');
        navigate('/student/scholarships');
      } else {
        alert('Đã lưu hồ sơ nhưng có lỗi khi gửi email thông báo!');
      }
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
      <div className="text-center py-8">
        <div className="text-lg text-red-600">Không tìm thấy học bổng!</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-red-600">Thông tin xét duyệt học bổng</h1>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Main Content */}
          <div className="flex-1 space-y-8">
            
            {/* Section 1: Thông tin chung */}
            <div id="section-1" className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center mr-3">1</div>
                <h2 className="text-lg font-semibold">Thông tin chung</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Tên học bổng *:</label>
                  <input 
                    type="text" 
                    value={scholarship.title}
                    disabled
                    className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Loại học bổng</label>
                    <input 
                      type="text" 
                      value={scholarship.type}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Số lượng học bổng</label>
                    <input 
                      type="text" 
                      value={scholarship.slots}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Giá trị học bổng/suất</label>
                    <input 
                      type="text" 
                      value={scholarship.value_per_slot?.toLocaleString('vi-VN')}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Đối tác cấp học bổng</label>
                    <input 
                      type="text" 
                      value={scholarship.sponsor}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Ngày bắt đầu đăng ký *</label>
                    <input 
                      type="text" 
                      value={new Date(scholarship.register_start_at).toLocaleString('vi-VN')}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Ngày kết thúc đăng ký *</label>
                    <input 
                      type="text" 
                      value={new Date(scholarship.register_end_at).toLocaleString('vi-VN')}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Dành cho sinh viên các đơn vị</label>
                    <textarea 
                      value={scholarship.target_departments}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 h-20"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Dành cho sinh viên các khóa</label>
                    <input 
                      type="text" 
                      value={scholarship.target_courses}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Dành cho sinh viên các hệ *</label>
                  <textarea 
                    value={scholarship.target_programs}
                    disabled
                    className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 h-16"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Cán bộ phụ trách</label>
                    <input 
                      type="text" 
                      value={scholarship.contact_person}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Thông tin liên hệ</label>
                    <input 
                      type="text" 
                      value={scholarship.contact_info}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Tài liệu</label>
                  {scholarship.document_url && (
                    <a 
                      href={scholarship.document_url}
                      target="_blank"
                      rel="noopener noreferrer" 
                      className="text-blue-600 hover:text-blue-800"
                    >
                      {scholarship.document_url.split('/').pop()}
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Section 2: Thông tin chi tiết */}
            <div id="section-2" className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center mr-3">2</div>
                <h2 className="text-lg font-semibold">Thông tin chi tiết</h2>
              </div>
              
              <div className="prose max-w-none">
                <div dangerouslySetInnerHTML={{ __html: scholarship.description || 'Không có mô tả chi tiết' }} />
              </div>
            </div>

            {/* Section 3: Thông tin đăng ký học bổng */}
            <div id="section-3" className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center mr-3">3</div>
                <h2 className="text-lg font-semibold">Thông tin đăng ký học bổng</h2>
              </div>

              <div className="space-y-6">
                {/* Thông tin tự động từ database */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm CPA *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_cpa || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm GPA *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_gpa || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm rèn luyện kỳ gần nhất *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_drl_latest || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tổng số tín chỉ tích lũy *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_total_credits || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm rèn luyện TB tích lũy *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_drl_average || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm TB 2 HK gần nhất *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_gpa_last_2_sem || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Điểm rèn luyện 2 kỳ gần nhất *</label>
                    <input 
                      type="text" 
                      value={autoData?.auto_drl_last_2_sem || ''}
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-lg bg-gray-100"
                    />
                  </div>
                </div>

                {/* Thông tin nhập tay */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Hoàn cảnh gia đình *</label>
                    <select 
                      value={formData.family_status}
                      onChange={(e) => setFormData(prev => ({ ...prev, family_status: e.target.value as any }))}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    >
                      <option value="Bình thường">Bình thường</option>
                      <option value="Khó khăn">Khó khăn</option>
                      <option value="Cận nghèo">Cận nghèo</option>
                      <option value="Nghèo">Nghèo</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Quốc gia</label>
                      <select 
                        value={formData.address_country}
                        onChange={(e) => setFormData(prev => ({ ...prev, address_country: e.target.value }))}
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      >
                        <option value="Việt Nam">Việt Nam</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Tỉnh/Thành phố</label>
                      <select 
                        value={formData.address_city}
                        onChange={(e) => setFormData(prev => ({ ...prev, address_city: e.target.value }))}
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      >
                        <option value="">Chọn tỉnh/thành</option>
                        <option value="Hà Nội">Hà Nội</option>
                        <option value="TP Hồ Chí Minh">TP Hồ Chí Minh</option>
                        {/* Add more cities */}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Quận/Huyện</label>
                      <select 
                        value={formData.address_ward}
                        onChange={(e) => setFormData(prev => ({ ...prev, address_ward: e.target.value }))}
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      >
                        <option value="">Chọn quận/huyện</option>
                        <option value="Phúc Lợi">Phúc Lợi</option>
                        {/* Add more districts */}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Địa chỉ chi tiết</label>
                      <input 
                        type="text" 
                        value={formData.address_detail}
                        onChange={(e) => setFormData(prev => ({ ...prev, address_detail: e.target.value }))}
                        placeholder="số 8, ngách 201/19, tổ 5, Phúc Lợi"
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Số điện thoại hiện tại *</label>
                    <input 
                      type="text" 
                      value={formData.phone_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, phone_number: e.target.value }))}
                      placeholder="Nhập số điện thoại"
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">STK nhận học bổng nếu đạt *</label>
                      <input 
                        type="text" 
                        value={formData.bank_account_number}
                        onChange={(e) => setFormData(prev => ({ ...prev, bank_account_number: e.target.value }))}
                        placeholder="Nhập số tài khoản chính chủ, lưu ý"
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Tại ngân hàng nào (VD: BIDV, Vietinbank, ...)</label>
                      <input 
                        type="text" 
                        value={formData.bank_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, bank_name: e.target.value }))}
                        placeholder="Nhập tên ngân hàng"
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>

                {/* Text areas */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Mô tả ngắn gọn hoàn cảnh gia đình</label>
                    <textarea 
                      value={formData.family_description}
                      onChange={(e) => setFormData(prev => ({ ...prev, family_description: e.target.value }))}
                      placeholder="Nhập không quá 300 từ"
                      rows={4}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Thành tích học tập, NCKH đạt được khen thưởng trong thời gian học tập tại 
                      Đại học Bách khoa Hà Nội (Yêu cầu tài minh chứng lên)
                    </label>
                    <textarea 
                      value={formData.achievement_special}
                      onChange={(e) => setFormData(prev => ({ ...prev, achievement_special: e.target.value }))}
                      rows={4}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Thành tích hoạt động phong trào Đoàn - Hội được khen thưởng trong thời gian 
                      học tập tại Đại học Bách khoa Hà Nội (tài minh chứng lên)
                    </label>
                    <textarea 
                      value={formData.achievement_activity}
                      onChange={(e) => setFormData(prev => ({ ...prev, achievement_activity: e.target.value }))}
                      rows={4}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Lý do xin học bổng và cam kết của sinh viên
                    </label>
                    <textarea 
                      value={formData.reason_apply}
                      onChange={(e) => setFormData(prev => ({ ...prev, reason_apply: e.target.value }))}
                      rows={4}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 4: Nộp hồ sơ đính kèm */}
            <div id="section-4" className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center mr-3">4</div>
                <h2 className="text-lg font-semibold">Nộp hồ sơ đính kèm</h2>
              </div>

              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  <strong>Sinh viên tải các hồ sơ đính kèm:</strong><br />
                  <strong>Chú ý:</strong> Chỉ có thể tải lên file định (.png, .jpg, .jpeg) hoặc PDF (.pdf)
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Minh chứng hoàn cảnh khó khăn của gia đình có xác nhận của địa phương (nếu có)
                    </label>
                    <button className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-red-500 hover:bg-red-50">
                      <div className="text-red-500">↑</div>
                      <div className="text-sm text-gray-500">Tải file lên</div>
                    </button>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Bài viết ngắn gọn giới thiệu bản thân, năng lực học tập, mong muốn có nhận trong tương lai
                    </label>
                    <button className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-red-500 hover:bg-red-50">
                      <div className="text-red-500">↑</div>
                      <div className="text-sm text-gray-500">Tải file lên</div>
                    </button>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Các giấy khen (nếu có)
                    </label>
                    <button className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-red-500 hover:bg-red-50">
                      <div className="text-red-500">↑</div>
                      <div className="text-sm text-gray-500">Tải file lên</div>
                    </button>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Đơn xin học bổng (theo mẫu đính kèm thông báo)
                    </label>
                    <button className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-red-500 hover:bg-red-50">
                      <div className="text-red-500">↑</div>
                      <div className="text-sm text-gray-500">Tải file lên</div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Navigation */}
          <div className="w-80">
            <div className="bg-white rounded-lg shadow-sm p-4 sticky top-6">
              <h3 className="font-semibold text-red-600 mb-4">Mục lục</h3>
              <nav className="space-y-2">
                <button
                  onClick={() => scrollToSection(1)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeSection === 1 ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  1. Thông tin chung
                </button>
                <button
                  onClick={() => scrollToSection(2)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeSection === 2 ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  2. Thông tin chi tiết
                </button>
                <button
                  onClick={() => scrollToSection(3)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeSection === 3 ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  3. Thông tin đăng ký học bổng
                </button>
                <button
                  onClick={() => scrollToSection(4)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeSection === 4 ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  4. Nộp hồ sơ đính kèm
                </button>
              </nav>

              <div className="mt-6 space-y-3">
                <button
                  onClick={handleSave}
                  className="w-full bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-50"
                >
                  Lưu
                </button>
                <button
                  onClick={handleSubmit}
                  className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700"
                >
                  Nộp hồ sơ
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