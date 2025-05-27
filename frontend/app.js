$(function () {
  function sendProcess(target) {
    $.post(`/api/${target}`, {}, function (data) {
      const img = `<img src="data:image/png;base64,${data.image}" />`;
      $(`#cell-${target}`).html(img);
    });
  }

  $('.proc-btn').on('click', function () {
    const target = $(this).data('target');
    sendProcess(target);
  });

  $('#chat-send').on('click', function () {
    const prompt = $('#chat-input').val();
    const model = $('#chat-model').val();
    $('#chat-log').append(`<div class='user'><strong>You:</strong> ${prompt}</div>`);
    $.post('/api/chat', JSON.stringify({ prompt: prompt, model: model }), function (data) {
      $('#chat-log').append(`<div class='llm'><strong>LLM:</strong> ${data.response}</div>`);
    }, 'json');
    $('#chat-input').val('');
  });
});
