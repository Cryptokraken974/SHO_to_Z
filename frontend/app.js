$(function () {
  let selectedLazFile = "input/lion_takanawa.copc.laz"; // Default file

  // Accordion functionality
  $('#laz-accordion').on('click', function() {
    const content = $('#laz-content');
    const arrow = $('.accordion-arrow');

    if (content.hasClass('collapsed')) {
      content.removeClass('collapsed');
      arrow.css('transform', 'rotate(0deg)');
    } else {
      content.addClass('collapsed');
      arrow.css('transform', 'rotate(-90deg)');
    }
  });

  // Browse files button
  $('#browse-files').on('click', function() {
    loadFiles();
    $('#file-modal').show();
  });

  // Close modal
  $('.close, #cancel-select').on('click', function() {
    $('#file-modal').hide();
  });

  // Close modal when clicking outside
  $('#file-modal').on('click', function(e) {
    if (e.target === this) {
      $(this).hide();
    }
  });

  // File search functionality
  $('#file-search-input').on('input', function() {
    const searchTerm = $(this).val().toLowerCase();
    $('.file-item').each(function() {
      const fileName = $(this).text().toLowerCase();
      if (fileName.includes(searchTerm)) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });

  // File selection
  $(document).on('click', '.file-item', function() {
    $('.file-item').removeClass('selected');
    $(this).addClass('selected');
  });

  // Select file button
  $('#select-file').on('click', function() {
    const selectedFile = $('.file-item.selected').data('file');
    if (selectedFile) {
      selectedLazFile = selectedFile;
      $('#selected-file-name').text(selectedFile.split('/').pop());
      $('#file-modal').hide();
    }
  });

  // Load files from server
  function loadFiles() {
    $.get('/api/list-laz-files', function(data) {
      const fileList = $('#file-list');
      fileList.empty();

      data.files.forEach(function(file) {
        const fileItem = $(`<div class="file-item" data-file="${file}">${file}</div>`);
        fileList.append(fileItem);
      });
    }).fail(function() {
      // Fallback with mock data if endpoint doesn't exist yet
      const mockFiles = [
        'input/lion_takanawa.copc.laz',
        'input/CUI_A01_10-03/CUI_A01_10-03.laz'
      ];
      const fileList = $('#file-list');
      fileList.empty();

      mockFiles.forEach(function(file) {
        const fileItem = $(`<div class="file-item" data-file="${file}">${file}</div>`);
        fileList.append(fileItem);
      });
    });
  }

  function sendProcess(target) {
    console.log('sendProcess called with target:', target);
    console.log('selectedLazFile:', selectedLazFile);
    
    // Use the selected LAZ file
    $.post(`/api/${target}`, { input_file: selectedLazFile }, function (data) {
      console.log('Success response:', data);
      const img = `<img src="data:image/png;base64,${data.image}" />`;
      $(`#cell-${target}`).html(img);
    }).fail(function(xhr, status, error) {
      console.error('Request failed:', status, error);
      console.error('Response:', xhr.responseText);
    });
  }

  $('.proc-btn[data-target]').on('click', function () {
    const target = $(this).data('target');
    console.log('Button clicked, target:', target);
    console.log('Button element:', this);
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
