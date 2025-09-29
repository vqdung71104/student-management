import { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel } from 'docx'
import { saveAs } from 'file-saver'

export interface FormData {
  formType: string
  studentName: string
  studentId: string
  course: string
  class: string
  email: string
  phone?: string
  address?: string
  reason?: string
  purpose?: string
  details?: string
  [key: string]: any
}

export const generateDocument = async (formData: FormData): Promise<Blob> => {
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        // Header
        new Paragraph({
          children: [
            new TextRun({
              text: "ĐẠI HỌC BÁCH KHOA HÀ NỘI",
              bold: true,
              size: 28,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "TRƯỜNG CÔNG NGHỆ THÔNG TIN",
              bold: true,
              size: 28,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "VÀ TRUYỀN THÔNG",
              bold: true,
              size: 28,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
        }),
        
        new Paragraph({
          children: [
            new TextRun({
              text: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
              bold: true,
              size: 24,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "Độc lập – Tự do – Hạnh phúc",
              bold: true,
              size: 24,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
        }),

        // Title
        new Paragraph({
          children: [
            new TextRun({
              text: getFormTitle(formData.formType),
              bold: true,
              size: 32,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
        }),

        // Content
        new Paragraph({
          children: [
            new TextRun({
              text: `Kính gửi: ${getRecipient(formData.formType)}`,
              size: 24,
            }),
          ],
          spacing: { after: 300 },
        }),

        // Student info
        new Paragraph({
          children: [
            new TextRun({
              text: `Tôi là: ${formData.studentName}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: `MSSV: ${formData.studentId}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: `Lớp: ${formData.class}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: `Khóa: ${formData.course}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: `Email: ${formData.email}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        }),

        // Phone if provided
        ...(formData.phone ? [new Paragraph({
          children: [
            new TextRun({
              text: `Số điện thoại: ${formData.phone}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        })] : []),

        // Address if provided
        ...(formData.address ? [new Paragraph({
          children: [
            new TextRun({
              text: `Địa chỉ: ${formData.address}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        })] : []),

        // Main content
        new Paragraph({
          children: [
            new TextRun({
              text: getFormContent(formData),
              size: 24,
            }),
          ],
          spacing: { after: 300 },
        }),

        // Reason if provided
        ...(formData.reason ? [new Paragraph({
          children: [
            new TextRun({
              text: `Lý do: ${formData.reason}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        })] : []),

        // Purpose if provided
        ...(formData.purpose ? [new Paragraph({
          children: [
            new TextRun({
              text: `Mục đích sử dụng: ${formData.purpose}`,
              size: 24,
            }),
          ],
          spacing: { after: 200 },
        })] : []),

        // Details if provided
        ...(formData.details ? [new Paragraph({
          children: [
            new TextRun({
              text: `Chi tiết: ${formData.details}`,
              size: 24,
            }),
          ],
          spacing: { after: 300 },
        })] : []),

        // Closing
        new Paragraph({
          children: [
            new TextRun({
              text: "Tôi xin chân thành cảm ơn!",
              size: 24,
            }),
          ],
          spacing: { after: 400 },
        }),

        // Signature section
        new Paragraph({
          children: [
            new TextRun({
              text: `Hà Nội, ngày ${new Date().getDate()} tháng ${new Date().getMonth() + 1} năm ${new Date().getFullYear()}`,
              size: 24,
            }),
          ],
          alignment: AlignmentType.RIGHT,
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "Sinh viên",
              bold: true,
              size: 24,
            }),
          ],
          alignment: AlignmentType.RIGHT,
          spacing: { after: 300 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: formData.studentName,
              size: 24,
            }),
          ],
          alignment: AlignmentType.RIGHT,
        }),
      ],
    }],
  })

  return await Packer.toBlob(doc)
}

const getFormTitle = (formType: string): string => {
  const titles: { [key: string]: string } = {
    'student-certificate': 'GIẤY XÁC NHẬN SINH VIÊN',
    'student-introduction': 'GIẤY GIỚI THIỆU SINH VIÊN',
    'transcript-request': 'ĐƠN XIN CẤP BẢNG ĐIỂM',
    'graduation-certificate': 'ĐƒN XIN CẤP CHỨNG CHỈ TỐT NGHIỆP',
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

const getRecipient = (formType: string): string => {
  return "Ban Giám hiệu Trường Công nghệ Thông tin và Truyền thông"
}

const getFormContent = (formData: FormData): string => {
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
  return contents[formData.formType] || 'Tôi viết đơn này đề nghị Nhà trường hỗ trợ.'
}

export const downloadDocument = async (formData: FormData) => {
  const blob = await generateDocument(formData)
  const fileName = `${getFormTitle(formData.formType)}_${formData.studentName}_${formData.studentId}.docx`
  saveAs(blob, fileName)
  return blob
}