// public/pcm-processor.js

class PcmProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    // 从构造函数选项中获取目标采样率，默认为24000
    this.targetSampleRate = options.processorOptions.targetSampleRate || 24000;
    this.sourceSampleRate = 0; // 将在第一次处理时设置
    this.resampleRatio = 1;

    // 用于重采样的缓冲区
    this.buffer = [];
  }

  process(inputs, outputs, parameters) {
    // 我们只关心第一个输入
    const input = inputs[0];
    if (input.length === 0) {
      return true; // 没有输入数据，继续运行
    }

    // 获取第一个通道的数据
    const channelData = input[0];

    // 如果源采样率未设置，现在设置它
    if (this.sourceSampleRate === 0) {
      this.sourceSampleRate = sampleRate; // 'sampleRate' 是全局可用的
      this.resampleRatio = this.sourceSampleRate / this.targetSampleRate;
      console.log(`AudioWorklet: Source SR=${this.sourceSampleRate}, Target SR=${this.targetSampleRate}, Ratio=${this.resampleRatio}`);
    }

    // 将新数据添加到缓冲区
    this.buffer.push(...channelData);

    const outputSamples = [];
    
    // 执行重采样
    while (this.buffer.length >= this.resampleRatio) {
      let R = Math.floor(this.resampleRatio);
      let resampledValue = 0;
      for (let i = 0; i < R; i++) {
        resampledValue += this.buffer[i];
      }
      resampledValue /= R;
      outputSamples.push(resampledValue);

      // 从缓冲区移除已处理的样本
      this.buffer.splice(0, R);
    }

    if (outputSamples.length === 0) {
      return true;
    }

    // 将浮点样本转换为16位PCM
    const pcm16Data = new Int16Array(outputSamples.length);
    for (let i = 0; i < outputSamples.length; i++) {
      const sample = Math.max(-1, Math.min(1, outputSamples[i]));
      pcm16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    }

    // 将处理后的PCM数据发送回主线程
    // 我们发送原始缓冲区以避免复制
    this.port.postMessage(pcm16Data.buffer, [pcm16Data.buffer]);

    return true; // 保持处理器活动
  }
}

registerProcessor('pcm-processor', PcmProcessor); 