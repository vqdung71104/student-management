import { useState, useEffect } from 'react'

// FAQ Data
const faqData = [
  {
    id: 1,
    question: "Làm thế nào để đăng ký học phần?",
    answer: "Để đăng ký học phần, bạn cần: 1) Đăng nhập vào hệ thống, 2) Vào mục 'Đăng ký học phần', 3) Chọn các môn học muốn đăng ký, 4) Kiểm tra thời khóa biểu, 5) Xác nhận đăng ký."
  },
  {
    id: 2,
    question: "Tôi có thể hủy đăng ký học phần đã đăng ký không?",
    answer: "Có, bạn có thể hủy đăng ký trong thời gian cho phép (thường là trong 2 tuần đầu của học kỳ). Vào mục 'Quản lý đăng ký' để hủy."
  },
  {
    id: 3,
    question: "Làm thế nào để xem điểm số?",
    answer: "Điểm số sẽ được cập nhật trong mục 'Điểm số' sau khi giảng viên nhập điểm. Bạn có thể xem điểm theo từng môn học hoặc theo học kỳ."
  },
  {
    id: 4,
    question: "Tôi quên mật khẩu thì làm sao?",
    answer: "Liên hệ với bộ phận kỹ thuật qua email: support@soict.hust.edu.vn hoặc đến trực tiếp phòng Đào tạo để được hỗ trợ reset mật khẩu."
  },
  {
    id: 5,
    question: "Làm thế nào để đăng ký đồ án/thực tập?",
    answer: "Vào mục 'Đồ án/Thực tập', xem danh sách đề tài, đăng ký nguyện vọng (tối đa 3 nguyện vọng), và chờ giảng viên/doanh nghiệp duyệt."
  },
  {
    id: 6,
    question: "Thời gian đăng ký học phần là khi nào?",
    answer: "Thời gian đăng ký thường bắt đầu 2-3 tuần trước khi học kỳ mới bắt đầu. Thông báo cụ thể sẽ được đăng trên trang chủ hệ thống."
  },
  {
    id: 7,
    question: "Tôi có thể đăng ký vượt số tín chỉ tối đa không?",
    answer: "Không, hệ thống sẽ không cho phép đăng ký vượt quá số tín chỉ tối đa quy định (thường là 22 tín chỉ/học kỳ). Sinh viên có GPA cao có thể được phép đăng ký thêm."
  },
  {
    id: 8,
    question: "Làm sao để kiểm tra lịch thi?",
    answer: "Lịch thi sẽ được công bố trong mục 'Lịch thi' trước kỳ thi 2-3 tuần. Bạn có thể xem và in lịch thi cá nhân từ hệ thống."
  }
]

const UserGuide = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-blue-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">HƯỚNG DẪN SỬ DỤNG</h1>
        </div>
        
        <div className="p-6 space-y-8">
          {/* Section A */}
          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-4">A. Quy trình đăng ký Đồ án/Thực tập</h2>
            <div className="space-y-3">
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">1</span>
                <p>GV/DN cập nhật danh sách Đề tài trên hệ thống <a href="https://qldt.hust.edu.vn" className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">https://qldt.hust.edu.vn</a></p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">2</span>
                <p>SV đăng nhập hệ thống (<a href="https://qldt.hust.edu.vn" className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">https://qldt.hust.edu.vn</a>) để tham khảo các đề tài, đăng ký nguyện vọng (Thường là 3 nguyện vọng) đồng thời cung cấp các thông tin cần thiết (CV, điểm tiếng Anh, điểm CPA, ...).</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">3</span>
                <p>GV/DN duyệt nguyện vọng, có thể yêu cầu gặp/phỏng vấn, và xác nhận về nguyện vọng</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">4</span>
                <p>Nếu GV/DN đồng ý với nguyên vọng, việc đăng ký hoàn thành, SV sẽ tự liên hệ với GV/DN cho các bước tiếp theo</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">5</span>
                <p>Nếu GV/DN từ chối nguyện vọng, SV sẽ được chuyển xuống nguyện vọng tiếp theo</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">6</span>
                <p>Nếu hết các nguyện vọng mà SV không được nhận, Trường sẽ tự phân công SV cho một GV/DN có thể tiếp nhận</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">7</span>
                <p>Kết thúc Đồ án/Thực tập, SV sẽ nộp báo cáo và kết quả online đồng thời đánh giá, phản hồi về GV/DN</p>
              </div>
              
              <div className="flex">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-3 font-semibold">8</span>
                <p>GV/DN đánh giá, phản hồi đối với SV trên hệ thống</p>
              </div>
            </div>
            
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="font-semibold text-yellow-800 mb-2">Lưu ý:</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Việc đăng ký trên hệ thống QLĐT chỉ nhằm mục đích hỗ trợ SV theo nguyện vọng, KHÔNG thay thế cho việc đăng ký trên hệ thống SIS</li>
                <li>• Trường hợp SV không nhìn thấy DN mình mong muốn thực tập trên hệ thống, SV chủ động thông báo doanh nghiệp liên hệ với Bộ phận phụ trách thực tập doanh nghiệp để kiểm tra điều kiện nhận sinh viên thực tập và tuân thủ qui trình của nhà trường, thống nhất phương pháp giám sát và đánh giá sinh viên, đảm bảo quyền lợi sinh viên khi thực tập doanh nghiệp cũng như đảm bảo qui tắc đánh giá kết quả thực tập của sinh viên. Trường không gửi sinh viên đi thực tập tại các doanh nghiệp không liên hệ với nhà trường để thực hiện thỏa mãn các điều kiện trên.</li>
              </ul>
            </div>
          </section>
          
          {/* Section B */}
          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-4">B. Làm thế nào để DN có thể tiếp nhận SV thực tập</h2>
            <div className="space-y-3">
              <div className="flex">
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded mr-3 font-semibold">1</span>
                <p>Để có thể tiếp nhận SV thực tập, DN phải đăng ký tài khoản và điền đầy đủ thông tin trên hệ thống quản lý của Viện (<a href="https://cam.soict.ai" className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">https://cam.soict.ai</a>) để Trường có thể đánh giá về khả năng tiếp nhận của DN, bao gồm về lĩnh vực, quy mô, chương trình thực tập, đào tạo, độ phù hợp so với chương trình đào tạo, ...</p>
              </div>
              
              <div className="flex">
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded mr-3 font-semibold">2</span>
                <div>
                  <p className="mb-2">Trong trường hợp cần hỗ trợ, quý DN liên hệ trực tiếp với Bộ phận hợp tác Doanh nghiệp của Trường:</p>
                  <div className="ml-4 space-y-1 text-sm">
                    <p>• Phạm Ánh Tuyết: <a href="mailto:tuyetpta@soict.hust.edu.vn" className="text-blue-600">tuyetpta@soict.hust.edu.vn</a> - 0982105519</p>
                    <p>• Nguyễn Tuấn Hải: <a href="mailto:haintu@soict.hust.edu.vn" className="text-blue-600">haintu@soict.hust.edu.vn</a> - 0983331526</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
          
          {/* Section C */}
          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-4">C. Thời lượng và đối tượng của kỳ thực tập DN như thế nào?</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-300">
                <thead className="bg-blue-50">
                  <tr>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Tên đợt thực tập</th>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Thời gian thực tập</th>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Thời lượng thực tập tối thiểu</th>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Đối tượng thực tập</th>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Số lượng SV (dự kiến)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">Thực tập doanh nghiệp học kỳ I</td>
                    <td className="border border-gray-300 px-4 py-2">Đầu tháng 9 đến giữa tháng 12</td>
                    <td className="border border-gray-300 px-4 py-2">
                      • Hệ kỹ sư: 160 giờ bán thời gian (part-time) hoặc tương đương<br/>
                      • Hệ cử nhân: 600 giờ toàn thời gian (full-time) hoặc tương đương
                    </td>
                    <td className="border border-gray-300 px-4 py-2">Sinh viên năm 3, 4, 5</td>
                    <td className="border border-gray-300 px-4 py-2">250 - 400</td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="border border-gray-300 px-4 py-2">Thực tập doanh nghiệp học kỳ II</td>
                    <td className="border border-gray-300 px-4 py-2">Giữa tháng 1 đến cuối tháng 5</td>
                    <td className="border border-gray-300 px-4 py-2">160 giờ bán thời gian (part-time) hoặc tương đương</td>
                    <td className="border border-gray-300 px-4 py-2">Sinh viên năm 3, 4, 5</td>
                    <td className="border border-gray-300 px-4 py-2">80 - 100</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">Thực tập doanh nghiệp học kỳ hè</td>
                    <td className="border border-gray-300 px-4 py-2">Giữa tháng 6 đến giữa tháng 8 hàng năm</td>
                    <td className="border border-gray-300 px-4 py-2">
                      • Hệ kỹ sư: 160 giờ bán thời gian (part-time) hoặc tương đương<br/>
                      • Hệ cử nhân: 600 giờ toàn thời gian (full-time) hoặc tương đương
                    </td>
                    <td className="border border-gray-300 px-4 py-2">Sinh viên năm 3, 4, 5</td>
                    <td className="border border-gray-300 px-4 py-2">300 - 400</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

const FAQ = () => {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)
  const [faqs, setFaqs] = useState<Array<{id: number, question: string, answer: string}>>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchFAQs = async () => {
      try {
        const response = await fetch('http://localhost:8000/faq?active_only=true')
        if (response.ok) {
          const data = await response.json()
          setFaqs(data)
        } else {
          // Fallback to default FAQs if API fails
          setFaqs(faqData)
        }
      } catch (error) {
        console.error('Error fetching FAQs:', error)
        // Fallback to default FAQs
        setFaqs(faqData)
      } finally {
        setLoading(false)
      }
    }

    fetchFAQs()
  }, [])

  const toggleFaq = (id: number) => {
    setExpandedFaq(expandedFaq === id ? null : id)
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md">
          <div className="bg-green-600 text-white p-6 rounded-t-lg">
            <h1 className="text-2xl font-bold">NHỮNG CÂU HỎI THƯỜNG GẶP</h1>
          </div>
          <div className="p-6 flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-green-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">NHỮNG CÂU HỎI THƯỜNG GẶP</h1>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div key={faq.id} className="border border-gray-200 rounded-lg">
                <button
                  onClick={() => toggleFaq(faq.id)}
                  className="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 rounded-t-lg flex justify-between items-center transition-colors"
                >
                  <span className="font-semibold text-gray-800">{faq.question}</span>
                  <svg
                    className={`w-5 h-5 transform transition-transform ${
                      expandedFaq === faq.id ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {expandedFaq === faq.id && (
                  <div className="px-4 py-3 border-t border-gray-200 bg-white rounded-b-lg">
                    <p className="text-gray-700">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const Feedback = () => {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    subject: '',
    feedback: '',
    suggestions: '',
    email: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('Cảm ơn bạn đã gửi phản hồi! Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.')
        setShowForm(false)
        setFormData({ subject: '', feedback: '', suggestions: '', email: '' })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to submit feedback')
      }
    } catch (error) {
      console.error('Error submitting feedback:', error)
      alert('Có lỗi xảy ra khi gửi phản hồi. Vui lòng thử lại sau.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (showForm) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md">
          <div className="bg-purple-600 text-white p-6 rounded-t-lg flex justify-between items-center">
            <h1 className="text-2xl font-bold">PHẢN HỒI VÀ GÓP Ý</h1>
            <button
              onClick={() => setShowForm(false)}
              className="text-white hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email của bạn *
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="your.email@example.com"
              />
            </div>

            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                Chủ đề *
              </label>
              <select
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Chọn chủ đề</option>
                <option value="bug">Báo lỗi hệ thống</option>
                <option value="feature">Đề xuất tính năng mới</option>
                <option value="ui">Giao diện người dùng</option>
                <option value="performance">Hiệu suất hệ thống</option>
                <option value="content">Nội dung thông tin</option>
                <option value="other">Khác</option>
              </select>
            </div>

            <div>
              <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
                Phản ánh của bạn về hệ thống *
              </label>
              <textarea
                id="feedback"
                name="feedback"
                value={formData.feedback}
                onChange={handleInputChange}
                required
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Mô tả chi tiết vấn đề bạn gặp phải hoặc nhận xét về hệ thống..."
              />
            </div>

            <div>
              <label htmlFor="suggestions" className="block text-sm font-medium text-gray-700 mb-2">
                Đóng góp của bạn về hệ thống
              </label>
              <textarea
                id="suggestions"
                name="suggestions"
                value={formData.suggestions}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Ý kiến đóng góp để cải thiện hệ thống..."
              />
            </div>

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Đang gửi...' : 'Gửi phản hồi'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-purple-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">PHẢN HỒI VÀ GÓP Ý</h1>
        </div>
        
        <div className="p-6 text-center">
          <div className="mb-6">
            <div className="w-24 h-24 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-12 h-12 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Chia sẻ ý kiến của bạn</h2>
            <p className="text-gray-600">
              Chúng tôi luôn lắng nghe và trân trọng mọi phản hồi từ sinh viên để cải thiện hệ thống tốt hơn.
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-800 mb-3">Form phản hồi bao gồm:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div className="flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Chủ đề phản ánh
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Phản ánh về hệ thống
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Đóng góp cải thiện
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Thông tin liên hệ
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setShowForm(true)}
            className="bg-purple-600 text-white px-8 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium inline-flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-1M14 6h4a2 2 0 012 2v4M5 13l4 4L19 7" />
            </svg>
            Mở form phản hồi
          </button>
          
          <div className="mt-6 text-sm text-gray-500">
            <p>Phản hồi sẽ được gửi trực tiếp đến: <strong>vuquangdung71104@gmail.com</strong></p>
          </div>
        </div>
      </div>
    </div>
  )
}

export { UserGuide, FAQ, Feedback }