export interface Tool {
  id: string;
  name: string;
  subtitle: string;
  image: string;
  features: string[];
  rating: number;
  color: string;
  efficiency: string;
}

export const tools: Tool[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    subtitle: 'Anthropic 出品的 AI 编程助手',
    image: 'scene2_claude_code.png',
    features: [
      '理解整个代码库上下文',
      '自然语言驱动代码生成',
      '支持终端直接操作',
      '智能重构与 Bug 修复',
    ],
    rating: 5,
    color: '#7C3AED',
    efficiency: '40%',
  },
  {
    id: 'cursor',
    name: 'Cursor',
    subtitle: 'AI 原生的代码编辑器',
    image: 'scene3_cursor.png',
    features: [
      '内置 AI 对话与代码补全',
      '多文件上下文理解',
      '一键重构整个项目',
      '基于 VSCode 生态',
    ],
    rating: 5,
    color: '#3B82F6',
    efficiency: '30%',
  },
  {
    id: 'copilot',
    name: 'GitHub Copilot',
    subtitle: 'GitHub 与 OpenAI 联合打造',
    image: 'scene4_copilot.png',
    features: [
      '实时代码补全建议',
      '支持几乎所有编程语言',
      '与 GitHub 深度集成',
      'Copilot Chat 对话式编程',
    ],
    rating: 4,
    color: '#10B981',
    efficiency: '50%',
  },
  {
    id: 'v0',
    name: 'v0.dev',
    subtitle: 'Vercel 出品的 AI UI 生成器',
    image: 'scene5_v0.png',
    features: [
      '自然语言生成 React 组件',
      'Shadcn UI + Tailwind CSS',
      '所见即所得的预览',
      '一键导出到项目',
    ],
    rating: 4,
    color: '#F59E0B',
    efficiency: '70%',
  },
  {
    id: 'bolt',
    name: 'bolt.new',
    subtitle: '浏览器中的全栈 AI 开发',
    image: 'scene6_bolt.png',
    features: [
      '提示词直接生成完整应用',
      '内置终端与包管理',
      '一键部署到云端',
      '支持多种框架',
    ],
    rating: 4,
    color: '#EF4444',
    efficiency: '80%',
  },
];
