<template>
  <div class="smart-analysis-container">
    <div class="header">
      <h1 class="title">智能财报分析</h1>
      <p class="subtitle">基于大语言模型的智能财报分析，提供深度洞察和投资建议</p>
    </div>

    <!-- Step 1: Selection -->
    <div v-if="!analysisStarted" class="selection-container">
      <div class="card">
        <h2 class="card-title">选择要分析的财报</h2>
        <div class="form-grid">
          <!-- PDF Upload -->
          <div class="form-group full-width">
            <label>上传财报PDF</label>
            <div class="upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleFileDrop">
              <input ref="fileInput" type="file" accept=".pdf" @change="handleFileSelect" style="display: none;">
              <div v-if="!selectedFile" class="upload-placeholder">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>点击或拖拽上传PDF文件</p>
                <span>支持格式：PDF，最大50MB</span>
              </div>
              <div v-else class="upload-success">
                <i class="fas fa-file-pdf"></i>
                <p>{{ selectedFile.name }}</p>
                <span>{{ formatFileSize(selectedFile.size) }}</span>
              </div>
            </div>
          </div>

          <!-- AI Analysis Mode -->
          <div class="form-group full-width">
            <label>AI分析模式</label>
            <div class="mode-selection">
              <button class="mode-btn" :class="{ active: analysisMode === 'single' }" @click="analysisMode = 'single'">
                <i class="fas fa-file-alt"></i>
                <span>单篇分析</span>
              </button>
              <button class="mode-btn" :class="{ active: analysisMode === 'timeseries' }" @click="analysisMode = 'timeseries'">
                <i class="fas fa-chart-line"></i>
                <span>时间序列</span>
              </button>
              <button class="mode-btn" :class="{ active: analysisMode === 'peer' }" @click="analysisMode = 'peer'">
                <i class="fas fa-balance-scale"></i>
                <span>同行对比</span>
              </button>
              <button class="mode-btn" :class="{ active: analysisMode === 'industry' }" @click="analysisMode = 'industry'">
                <i class="fas fa-industry"></i>
                <span>行业分析</span>
              </button>
            </div>
          </div>

          <!-- Analysis Model -->
          <div class="form-group">
            <label for="analysis-model">分析模型</label>
            <select id="analysis-model" v-model="analysisModel">
              <option value="qwen-max">Qwen Max (推荐)</option>
              <option value="qwen-plus">Qwen Plus</option>
              <option value="qwen-turbo">Qwen Turbo</option>
            </select>
          </div>
        </div>
        <div class="start-button-container">
          <button @click="startAnalysis" class="start-btn" :disabled="!mockMode && !selectedFile">
            <i class="fas fa-cogs"></i>
            开始智能分析
          </button>
        </div>
      </div>
    </div>

    <!-- Loading Modal -->
    <div v-if="isLoading" class="loading-modal">
      <div class="loading-box">
        <div class="spinner"></div>
        <p>正在分析财报，请稍候...</p>
        <span>大型财报分析可能需要1-2分钟</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="progress-text">{{ progressText }}</p>
      </div>
    </div>

    <!-- Dual Window Interface -->
    <div v-if="analysisStarted && !isLoading" class="dual-window-container">
      <!-- Left Panel: Chat -->
      <div class="chat-panel">
        <div class="chat-header">
          <h3><i class="fas fa-comments"></i> 智能对话</h3>
          <button class="clear-chat-btn" @click="clearChat">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        <div class="chat-messages" ref="chatMessages">
          <div v-for="message in chatHistory" :key="message.id" class="message" :class="message.type">
            <div class="message-content">
              <div class="message-text">{{ message.text }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
          <div v-if="isTyping" class="message ai typing">
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <input 
            v-model="chatInput" 
            @keyup.enter="sendMessage" 
            placeholder="询问关于财报的任何问题..."
            :disabled="isTyping"
          >
          <button @click="sendMessage" :disabled="!chatInput.trim() || isTyping">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>

      <!-- Right Panel: Report Display -->
      <div class="report-panel">
        <div class="report-header">
          <h3><i class="fas fa-chart-bar"></i> 分析报告</h3>
          <div class="report-controls">
            <select v-model="selectedReport" @change="switchReport">
              <option v-for="report in savedReports" :key="report.id" :value="report.id">
                {{ report.name }}
              </option>
            </select>
            <button class="export-btn" @click="exportReport">
              <i class="fas fa-download"></i> 导出
            </button>
          </div>
        </div>
        
        <div class="report-tabs">
          <button 
            v-for="tab in reportTabs" 
            :key="tab.key" 
            class="tab-btn" 
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <i :class="tab.icon"></i>
            {{ tab.label }}
          </button>
        </div>

        <div class="report-content">
          <!-- Analysis Summary Tab -->
          <div v-if="activeTab === 'summary'" class="tab-content">
            <div class="summary-section">
              <h4>分析概要</h4>
              <div class="summary-cards">
                <div class="summary-card">
                  <div class="card-icon"><i class="fas fa-chart-line"></i></div>
                  <div class="card-content">
                    <h5>财务健康度</h5>
                    <div class="score">{{ mockData.healthScore }}/100</div>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: mockData.healthScore + '%' }"></div>
                    </div>
                  </div>
                </div>
                <div class="summary-card">
                  <div class="card-icon"><i class="fas fa-trending-up"></i></div>
                  <div class="card-content">
                    <h5>增长潜力</h5>
                    <div class="score">{{ mockData.growthPotential }}/100</div>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: mockData.growthPotential + '%' }"></div>
                    </div>
                  </div>
                </div>
                <div class="summary-card">
                  <div class="card-icon"><i class="fas fa-shield-alt"></i></div>
                  <div class="card-content">
                    <h5>风险评级</h5>
                    <div class="risk-level">{{ mockData.riskLevel }}</div>
                  </div>
                </div>
              </div>
              <div class="summary-text">
                <p>{{ mockData.summary }}</p>
              </div>
            </div>
          </div>

          <!-- Financial Indicators Tab -->
          <div v-if="activeTab === 'indicators'" class="tab-content">
            <div class="indicators-section">
              <h4>关键财务指标</h4>
              <div class="indicators-grid">
                <div v-for="indicator in mockData.indicators" :key="indicator.name" class="indicator-card">
                  <div class="indicator-header">
                    <span class="indicator-name">{{ indicator.name }}</span>
                    <span class="indicator-value" :class="indicator.trend">
                      {{ indicator.value }}
                      <i v-if="indicator.trend === 'up'" class="fas fa-arrow-up"></i>
                      <i v-if="indicator.trend === 'down'" class="fas fa-arrow-down"></i>
                      <i v-if="indicator.trend === 'stable'" class="fas fa-minus"></i>
                    </span>
                  </div>
                  <div class="indicator-description">{{ indicator.description }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Business Analysis Tab -->
          <div v-if="activeTab === 'business'" class="tab-content">
            <div class="business-section">
              <h4>业务分析</h4>
              <div class="analysis-blocks">
                <div v-for="block in mockData.businessAnalysis" :key="block.title" class="analysis-block">
                  <h5><i :class="block.icon"></i> {{ block.title }}</h5>
                  <p>{{ block.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Investment Advice Tab -->
          <div v-if="activeTab === 'advice'" class="tab-content">
            <div class="advice-section">
              <h4>投资建议</h4>
              <div class="advice-rating">
                <div class="rating-badge" :class="mockData.investmentRating.toLowerCase()">
                  {{ mockData.investmentRating }}
                </div>
                <div class="target-price">
                  目标价格: <strong>{{ mockData.targetPrice }}</strong>
                </div>
              </div>
              <div class="advice-content">
                <div class="pros-cons">
                  <div class="pros">
                    <h5><i class="fas fa-thumbs-up"></i> 优势</h5>
                    <ul>
                      <li v-for="pro in mockData.pros" :key="pro">{{ pro }}</li>
                    </ul>
                  </div>
                  <div class="cons">
                    <h5><i class="fas fa-thumbs-down"></i> 风险</h5>
                    <ul>
                      <li v-for="con in mockData.cons" :key="con">{{ con }}</li>
                    </ul>
                  </div>
                </div>
                <div class="advice-text">
                  <p>{{ mockData.adviceText }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Raw Data Tab -->
          <div v-if="activeTab === 'rawdata'" class="tab-content">
            <div class="rawdata-section">
              <h4>原始数据</h4>
              <div class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>指标</th>
                      <th>当期</th>
                      <th>上期</th>
                      <th>变化率</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in mockData.rawData" :key="item.metric">
                      <td>{{ item.metric }}</td>
                      <td>{{ item.current }}</td>
                      <td>{{ item.previous }}</td>
                      <td :class="item.change.startsWith('+') ? 'positive' : 'negative'">
                        {{ item.change }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, nextTick, onMounted } from 'vue';

interface ChatMessage {
  id: number;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
}

interface SavedReport {
  id: string;
  name: string;
  data: any;
}

export default defineComponent({
  name: 'SmartAnalysis',
  setup() {
    const analysisStarted = ref(false);
    const isLoading = ref(false);
    const progress = ref(0);
    const progressText = ref('');
    const selectedFile = ref<File | null>(null);
    const analysisMode = ref('single');
    const analysisModel = ref('qwen-max');
    const fileInput = ref<HTMLInputElement>();
    const mockMode = ref(true);
    
    // Chat related
    const chatHistory = ref<ChatMessage[]>([]);
    const chatInput = ref('');
    const isTyping = ref(false);
    const chatMessages = ref<HTMLElement>();
    
    // Report related
    const activeTab = ref('summary');
    const selectedReport = ref('current');
    const savedReports = ref<SavedReport[]>([
      { id: 'current', name: '当前分析报告', data: {} }
    ]);
    
    const reportTabs = [
      { key: 'summary', label: '分析概要', icon: 'fas fa-chart-pie' },
      { key: 'indicators', label: '财务指标', icon: 'fas fa-calculator' },
      { key: 'business', label: '业务分析', icon: 'fas fa-building' },
      { key: 'advice', label: '投资建议', icon: 'fas fa-lightbulb' },
      { key: 'rawdata', label: '原始数据', icon: 'fas fa-table' }
    ];

    // Mock data for demonstration
    const mockData = ref({
      healthScore: 78,
      growthPotential: 65,
      riskLevel: '中等',
      summary: '该公司财务状况整体良好，营收稳定增长，但需关注现金流状况。建议中长期持有，短期内可能面临行业调整压力。',
      investmentRating: '买入',
      targetPrice: '¥45.60',
      indicators: [
        { name: '营业收入', value: '¥123.45亿', trend: 'up', description: '同比增长15.2%' },
        { name: '净利润', value: '¥12.34亿', trend: 'up', description: '同比增长8.7%' },
        { name: '毛利率', value: '23.5%', trend: 'stable', description: '与上期基本持平' },
        { name: '资产负债率', value: '45.2%', trend: 'down', description: '较上期下降2.1%' },
        { name: 'ROE', value: '12.8%', trend: 'up', description: '净资产收益率提升' },
        { name: '现金比率', value: '1.25', trend: 'down', description: '流动性略有下降' }
      ],
      businessAnalysis: [
        {
          title: '主营业务',
          icon: 'fas fa-chart-bar',
          content: '公司主营业务收入稳定，核心产品市场占有率持续提升，新产品线贡献逐步显现。'
        },
        {
          title: '市场地位',
          icon: 'fas fa-trophy',
          content: '在细分领域保持领先地位，品牌影响力不断扩大，客户粘性较强。'
        },
        {
          title: '竞争优势',
          icon: 'fas fa-star',
          content: '技术研发实力雄厚，产业链布局完善，成本控制能力突出。'
        }
      ],
      pros: [
        '营收增长稳定，盈利能力强',
        '行业地位领先，市场份额稳固',
        '技术创新能力突出',
        '财务结构健康，负债率合理'
      ],
      cons: [
        '现金流状况需要关注',
        '行业竞争加剧',
        '原材料成本上涨压力',
        '汇率波动影响'
      ],
      adviceText: '基于综合分析，建议投资者采取中长期投资策略。公司基本面良好，但需密切关注现金流变化和行业发展趋势。',
      rawData: [
        { metric: '营业收入', current: '123.45亿', previous: '107.23亿', change: '+15.2%' },
        { metric: '净利润', current: '12.34亿', previous: '11.35亿', change: '+8.7%' },
        { metric: '总资产', current: '456.78亿', previous: '423.56亿', change: '+7.8%' },
        { metric: '净资产', current: '234.56亿', previous: '218.90亿', change: '+7.2%' },
        { metric: '经营现金流', current: '15.67亿', previous: '18.23亿', change: '-14.0%' }
      ]
    });

    const triggerFileUpload = () => {
      fileInput.value?.click();
    };

    const handleFileSelect = (event: Event) => {
      const target = event.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        selectedFile.value = target.files[0];
      }
    };

    const handleFileDrop = (event: DragEvent) => {
      event.preventDefault();
      if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
        selectedFile.value = event.dataTransfer.files[0];
      }
    };

    const formatFileSize = (bytes: number) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const startAnalysis = async () => {
      if (!mockMode.value && !selectedFile.value) return;
      
      isLoading.value = true;
      progress.value = 0;
      progressText.value = mockMode.value ? '正在准备分析 1...' : '正在上传文件...';
      
      try {
        if (!mockMode.value) {
          // 真实流程：上传并调用后端分析
          progress.value = 20;
          progressText.value = '正在上传PDF文件...';
          
          const formData = new FormData();
          formData.append('file', selectedFile.value as File);
          
          const uploadResponse = await fetch('/api/financial-reports/upload', {
            method: 'POST',
            body: formData
          });
          
          if (!uploadResponse.ok) {
            throw new Error('文件上传失败');
          }
          
          const uploadData = await uploadResponse.json();
          if (uploadData.code !== 200) {
            throw new Error(uploadData.message || '文件上传失败');
          }
          
          const fileId = uploadData.data.fileId;
          
          // Step 2: Start analysis
          progress.value = 40;
          progressText.value = '正在进行AI分析...';
          
          const analysisResponse = await fetch('/api/smart/analyze', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              fileId: fileId,
              stockCode: '000001',
              year: new Date().getFullYear(),
              reportType: 'annual',
              analysisMode: analysisMode.value,
              model: analysisModel.value,
              customRequirements: ''
            })
          });
          
          if (!analysisResponse.ok) {
            throw new Error('分析请求失败');
          }
          
          const analysisData = await analysisResponse.json();
          if (analysisData.code !== 200) {
            throw new Error(analysisData.message || '分析失败');
          }
          
          progress.value = 80;
          progressText.value = '正在生成报告...';
          
          if (analysisData.data) {
            mockData.value = {
              ...mockData.value,
              summary: analysisData.data.summary || mockData.value.summary,
            };
          }
          
          progress.value = 100;
          progressText.value = '分析完成！';
          
          await new Promise(resolve => setTimeout(resolve, 500));
          isLoading.value = false;
          analysisStarted.value = true;
          
          chatHistory.value.push({
            id: Date.now(),
            type: 'ai',
            text: '您好！我已经完成了财报分析。您可以查看右侧的分析报告，或者向我提问任何关于这份财报的问题。',
            timestamp: new Date()
          });
          
          saveToLocalStorage();
        } else {
          // 模拟流程：不调用后端，直接展示 mockData
          progress.value = 30;
          progressText.value = '正在进行AI分析 1...';
          await new Promise(resolve => setTimeout(resolve, 600));
          
          progress.value = 70;
          progressText.value = '正在生成报告 1...';
          await new Promise(resolve => setTimeout(resolve, 600));
          
          progress.value = 100;
          progressText.value = '分析完成 1！';
          await new Promise(resolve => setTimeout(resolve, 300));
          
          isLoading.value = false;
          analysisStarted.value = true;
          
          chatHistory.value.push({
            id: Date.now(),
            type: 'ai',
          text: '您好！已完成分析 1。右侧已生成分析报告，您也可以就报告内容继续提问。',
          timestamp: new Date()
        });
          
          saveToLocalStorage();
        }
      } catch (error: any) {
        isLoading.value = false;
        alert('分析失败: ' + (error.message || '未知错误'));
        console.error('Analysis error:', error);
      }
    };

    const sendMessage = async () => {
      if (!chatInput.value.trim() || isTyping.value) return;
      
      const userMessage: ChatMessage = {
        id: Date.now(),
        type: 'user',
        text: chatInput.value,
        timestamp: new Date()
      };
      
      chatHistory.value.push(userMessage);
      const question = chatInput.value;
      chatInput.value = '';
      isTyping.value = true;
      
      await nextTick();
      scrollToBottom();
      
      try {
        if (mockMode.value) {
          const summary = mockData.value.summary;
          const metrics = (mockData.value.indicators || []).slice(0, 3)
            .map((i: any) => `${i.name}:${i.value}（${i.description}）`)
            .join('；');
          const aiMessage: ChatMessage = {
            id: Date.now() + 1,
            type: 'ai',
            text: `这是回答 1：${summary}。核心指标：${metrics}。`,
            timestamp: new Date()
          };
          chatHistory.value.push(aiMessage);
          isTyping.value = false;
          await nextTick();
          scrollToBottom();
          saveToLocalStorage();
          return;
        }
        // Call the chat API
        const response = await fetch('/api/smart/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            question: question,
            sessionId: 'session_' + Date.now(), // 可以使用更好的会话管理
            fileId: 'current_file_id' // 需要保存当前分析的文件ID
          })
        });
        
        if (!response.ok) {
          throw new Error('聊天请求失败');
        }
        
        const data = await response.json();
        if (data.code !== 200) {
          throw new Error(data.message || '聊天失败');
        }
        
        const aiMessage: ChatMessage = {
          id: Date.now() + 1,
          type: 'ai',
          text: data.data.answer || '抱歉，我无法回答这个问题。',
          timestamp: new Date()
        };
        
        chatHistory.value.push(aiMessage);
        isTyping.value = false;
        await nextTick();
        scrollToBottom();
        saveToLocalStorage();
        
      } catch (error: any) {
        console.error('Chat error:', error);
        
        // Fallback to mock response on error
        const aiMessage: ChatMessage = {
          id: Date.now() + 1,
          type: 'ai',
          text: '抱歉，服务暂时不可用。请稍后再试。',
          timestamp: new Date()
        };
        
        chatHistory.value.push(aiMessage);
        isTyping.value = false;
        await nextTick();
        scrollToBottom();
        saveToLocalStorage();
      }
    };

    const clearChat = () => {
      chatHistory.value = [];
      saveToLocalStorage();
    };

    const scrollToBottom = () => {
      if (chatMessages.value) {
        chatMessages.value.scrollTop = chatMessages.value.scrollHeight;
      }
    };

    const formatTime = (ts: any) => {
      let date: Date;
      if (ts instanceof Date) {
        date = ts;
      } else {
        const d = new Date(ts);
        date = isNaN(d.getTime()) ? new Date() : d;
      }
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const switchReport = () => {
      // Switch between saved reports
      loadFromLocalStorage();
    };

    const exportReport = () => {
      // Export functionality
      alert('导出功能将在后续版本中实现');
    };

    const saveToLocalStorage = () => {
      const serializableChat = chatHistory.value.map((m: any) => ({
        ...m,
        timestamp: (m.timestamp instanceof Date)
          ? m.timestamp.toISOString()
          : new Date(m.timestamp).toISOString()
      }));
      const data = {
        chatHistory: serializableChat,
        analysisResult: mockData.value,
        selectedReport: selectedReport.value,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('smartAnalysis', JSON.stringify(data));
    };

    const loadFromLocalStorage = () => {
      const saved = localStorage.getItem('smartAnalysis');
      if (saved) {
        const data = JSON.parse(saved);
        const toDate = (v: any) => {
          try {
            if (v instanceof Date) return v;
            const d = new Date(v);
            if (!isNaN(d.getTime())) return d;
          } catch {}
          return new Date();
        };
        chatHistory.value = (data.chatHistory || []).map((m: any) => ({
          ...m,
          timestamp: toDate(m.timestamp)
        }));
        // Load other data as needed
      }
    };

    onMounted(() => {
      loadFromLocalStorage();
    });

    return {
      analysisStarted,
      isLoading,
      progress,
      progressText,
      selectedFile,
      analysisMode,
      analysisModel,
      fileInput,
      mockMode,
      chatHistory,
      chatInput,
      isTyping,
      chatMessages,
      activeTab,
      selectedReport,
      savedReports,
      reportTabs,
      mockData,
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      formatFileSize,
      startAnalysis,
      sendMessage,
      clearChat,
      formatTime,
      switchReport,
      exportReport
    };
  },
});
</script>

<style scoped>
.smart-analysis-container {
  padding: 2rem;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.title {
  font-size: 2.5rem;
  color: #1a2a4c;
  font-weight: 600;
}

.subtitle {
  font-size: 1.1rem;
  color: #5a6882;
}

.selection-container {
  max-width: 800px;
  margin: 0 auto;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  color: #1a2a4c;
  font-weight: 500;
  border-left: 4px solid #2962ff;
  padding-left: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2962ff;
}

/* Upload Area */
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #2962ff;
  background-color: #f8f9ff;
}

.upload-placeholder i {
  font-size: 3rem;
  color: #909399;
  margin-bottom: 1rem;
}

.upload-placeholder p {
  font-size: 1.1rem;
  color: #606266;
  margin-bottom: 0.5rem;
}

.upload-placeholder span {
  font-size: 0.9rem;
  color: #909399;
}

.upload-success {
  color: #67c23a;
}

.upload-success i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.upload-success p {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.upload-success span {
  font-size: 0.9rem;
  color: #909399;
}

.mode-selection {
  display: flex;
  gap: 1rem;
}

.mode-btn {
  flex-grow: 1;
  padding: 0.75rem;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.mode-btn:hover {
  border-color: #2962ff;
  color: #2962ff;
}

.mode-btn.active {
  background-color: #e9efff;
  border-color: #2962ff;
  color: #2962ff;
  font-weight: 500;
}

.start-button-container {
  margin-top: 2rem;
  text-align: center;
}

.start-btn {
  padding: 0.8rem 2.5rem;
  font-size: 1.1rem;
  background-color: #2962ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.start-btn:hover:not(:disabled) {
  background-color: #0039cb;
}

.start-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.loading-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-box {
  background: white;
  padding: 2rem 3rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  min-width: 300px;
}

.loading-box p {
  font-size: 1.2rem;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.loading-box span {
  font-size: 0.9rem;
  color: #666;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  margin: 1rem 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #2962ff;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.5rem;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2962ff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Dual Window Layout */
.dual-window-container {
  display: flex;
  gap: 1rem;
  height: calc(100vh - 200px);
  margin-top: 2rem;
}

/* Chat Panel */
.chat-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  max-width: 400px;
}

.chat-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  color: #1a2a4c;
  font-size: 1.2rem;
}

.clear-chat-btn {
  background: none;
  border: none;
  color: #909399;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-chat-btn:hover {
  background-color: #f5f7fa;
  color: #f56c6c;
}

.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  align-items: flex-start;
}

.message.user {
  justify-content: flex-end;
}

.message.ai {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  position: relative;
}

.message.user .message-content {
  background-color: #2962ff;
  color: white;
}

.message.ai .message-content {
  background-color: #f5f7fa;
  color: #333;
}

.message-text {
  margin-bottom: 0.25rem;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #909399;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input {
  padding: 1rem 1.5rem;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 0.5rem;
}

.chat-input input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  outline: none;
  font-size: 0.9rem;
}

.chat-input input:focus {
  border-color: #2962ff;
}

.chat-input button {
  background-color: #2962ff;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background-color: #0039cb;
}

.chat-input button:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

/* Report Panel */
.report-panel {
  flex: 2;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.report-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-header h3 {
  margin: 0;
  color: #1a2a4c;
  font-size: 1.2rem;
}

.report-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.report-controls select {
  padding: 0.5rem;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 0.9rem;
}

.export-btn {
  background-color: #67c23a;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
}

.export-btn:hover {
  background-color: #5daf34;
}

.report-tabs {
  display: flex;
  border-bottom: 1px solid #ebeef5;
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.9rem;
  color: #606266;
  transition: all 0.2s;
}

.tab-btn:hover {
  background-color: #f5f7fa;
  color: #2962ff;
}

.tab-btn.active {
  color: #2962ff;
  border-bottom: 2px solid #2962ff;
  background-color: #f8f9ff;
}

.report-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.tab-content h4 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #1a2a4c;
  font-size: 1.3rem;
}

/* Summary Tab */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  font-size: 2rem;
  color: #2962ff;
}

.card-content h5 {
  margin: 0 0 0.5rem 0;
  color: #606266;
  font-size: 0.9rem;
}

.score {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1a2a4c;
  margin-bottom: 0.5rem;
}

.score-bar {
  width: 100px;
  height: 6px;
  background-color: #ebeef5;
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background-color: #67c23a;
  transition: width 0.3s ease;
}

.risk-level {
  font-size: 1.2rem;
  font-weight: bold;
  color: #e6a23c;
}

.summary-text {
  background: #f5f7fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #2962ff;
}

.summary-text p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

/* Indicators Tab */
.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.indicator-card {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 1.5rem;
  border-left: 4px solid #2962ff;
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.indicator-name {
  font-weight: 500;
  color: #1a2a4c;
}

.indicator-value {
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.indicator-value.up {
  color: #67c23a;
}

.indicator-value.down {
  color: #f56c6c;
}

.indicator-value.stable {
  color: #909399;
}

.indicator-description {
  font-size: 0.9rem;
  color: #606266;
}

/* Business Analysis Tab */
.analysis-blocks {
  display: grid;
  gap: 1.5rem;
}

.analysis-block {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 1.5rem;
  border-left: 4px solid #2962ff;
}

.analysis-block h5 {
  margin: 0 0 1rem 0;
  color: #1a2a4c;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.analysis-block p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

/* Investment Advice Tab */
.advice-rating {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9ff;
  border-radius: 8px;
}

.rating-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: bold;
  font-size: 1.1rem;
}

.rating-badge.买入 {
  background-color: #67c23a;
  color: white;
}

.rating-badge.持有 {
  background-color: #e6a23c;
  color: white;
}

.rating-badge.卖出 {
  background-color: #f56c6c;
  color: white;
}

.target-price {
  font-size: 1.1rem;
  color: #1a2a4c;
}

.pros-cons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.pros, .cons {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 1.5rem;
}

.pros h5, .cons h5 {
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1a2a4c;
}

.pros h5 {
  color: #67c23a;
}

.cons h5 {
  color: #f56c6c;
}

.pros ul, .cons ul {
  margin: 0;
  padding-left: 1.5rem;
}

.pros li, .cons li {
  margin-bottom: 0.5rem;
  color: #606266;
  line-height: 1.5;
}

.advice-text {
  background: #f5f7fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #2962ff;
}

.advice-text p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

/* Raw Data Tab */
.data-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.data-table table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.data-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #1a2a4c;
}

.data-table tbody tr:hover {
  background-color: #f8f9ff;
}

.data-table .positive {
  color: #67c23a;
  font-weight: 500;
}

.data-table .negative {
  color: #f56c6c;
  font-weight: 500;
}

/* Font Awesome Icons */
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css");

/* Responsive Design */
@media (max-width: 1200px) {
  .dual-window-container {
    flex-direction: column;
    height: auto;
  }
  
  .chat-panel {
    max-width: none;
    height: 400px;
  }
  
  .pros-cons {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .smart-analysis-container {
    padding: 1rem;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .mode-selection {
    flex-direction: column;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .indicators-grid {
    grid-template-columns: 1fr;
  }
  
  .report-tabs {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: none;
    min-width: 120px;
  }
}
</style>