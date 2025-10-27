<template>
  <div class="chat-panel">
    <div v-if="notification" class="notification">
      {{ notification }}
    </div>
    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message-wrapper" :class="{ 'user-message': message.sender === 'user', 'bot-message': message.sender === 'bot' }">
        <div class="message-content">{{ message.text }}</div>
      </div>
      <div v-if="isLoading" class="message-wrapper bot-message">
        <div class="message-content">正在思考中...</div>
      </div>
    </div>
    <div class="input-container">
      <input type="text" v-model="userInput" @keyup.enter="sendMessage" placeholder="输入您的问题..." :disabled="!currentReportId" />
      <button @click="sendMessage" :disabled="!currentReportId || isLoading">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import axios from 'axios';

// 定义消息类型
interface Message {
  sender: 'user' | 'bot';
  text: string;
}

const props = defineProps<{ currentReportId: string }>();

const notification = ref('');
const messages = ref<Message[]>([]);
const userInput = ref('');
const isLoading = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || !props.currentReportId) {
    alert('请输入问题，并确保已选择一份报告。');
    return;
  }

  const userMessage: Message = { sender: 'user', text: userInput.value };
  messages.value.push(userMessage);
  const currentQuery = userInput.value;
  userInput.value = '';
  isLoading.value = true;
  scrollToBottom();

  try {
    const response = await axios.post('http://localhost:5000/api/smart/chat', {
      report_id: props.currentReportId,
      query: currentQuery,
    });

    if (response.data && response.data.answer) {
      const botMessage: Message = { sender: 'bot', text: response.data.answer };
      messages.value.push(botMessage);
    }
  } catch (error) {
    console.error('聊天请求失败:', error);
    const errorMessage: Message = { sender: 'bot', text: '抱歉，我暂时无法回答您的问题。' };
    messages.value.push(errorMessage);
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

// 监视报告ID变化
watch(() => props.currentReportId, (newId, oldId) => {
  if (newId) {
    messages.value = []; // 清空历史消息
    const reportName = localStorage.getItem(newId) ? JSON.parse(localStorage.getItem(newId)!).name : '';
    notification.value = `当前已切换至【${reportName}】，可以开始提问了。`;
    setTimeout(() => {
      notification.value = '';
    }, 4000);
  } else {
    notification.value = '请先选择一份报告进行分析和对话。';
    messages.value = [];
  }
}, { immediate: true });

</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.notification {
  padding: 10px;
  background-color: #e6f7ff;
  border-bottom: 1px solid #91d5ff;
  text-align: center;
  font-size: 14px;
  color: #096dd9;
}
.messages-container {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f5f5;
}
.message-wrapper {
  display: flex;
  margin-bottom: 15px;
}
.user-message {
  justify-content: flex-end;
}
.bot-message {
  justify-content: flex-start;
}
.message-content {
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 18px;
  line-height: 1.5;
}
.user-message .message-content {
  background-color: #1890ff;
  color: white;
  border-bottom-right-radius: 5px;
}
.bot-message .message-content {
  background-color: #fff;
  color: #333;
  border: 1px solid #e8e8e8;
  border-bottom-left-radius: 5px;
}
.input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #d9d9d9;
}
input {
  flex-grow: 1;
  padding: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}
button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

button {
  margin-left: 10px;
  padding: 8px 15px;
  border: none;
  background-color: #1890ff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
</style>