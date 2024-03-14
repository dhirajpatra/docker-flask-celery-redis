// custom javascript

$( document ).ready(() => {
  console.log('Sanity Check Presto!');
  url = 'http://' + $(location).attr('hostname') + ':9181';
  console.log(url)
  $('#qr_dashboard').attr('src', url);

  $.ajax({
    url: '/all_tasks',
    method: 'GET'
  })
  .done((res) => {
    var html = `
        <tr>
          <td>Total: ${res.data.total}</td>
        </tr>`
        
    var tasks = res.data.tasks;
    $.each( tasks, function( key, value ) {
      console.log( key + ": " + value );
      html += `<tr><td>${key}</td><td><a href="/tasks/${value}" target="_blank">${value}</a></td></tr>`
    });

    $('#alltasks').prepend(html);

    setTimeout(function() {
      location.reload();
    }, 50000);

  })
  .fail((err) => {
    console.log(err)
  });


  $('.btn').on('click', function() {
    $.ajax({
      url: '/task',
      data: { type: $(this).data('type') },
      method: 'POST'
    })
    .done((res) => {
      getStatus(res.data.task_id)
    })
    .fail((err) => {
      console.log(err)
    });
  });
  
  function getStatus(taskID) {
    $.ajax({
      url: `/task_status/${taskID}`,
      method: 'GET'
    })
    .done((res) => {
      const html = `
        <tr>
          <td>${res.data.task_id}</td>
          <td>${res.data.task_status}</td>
          <td>${res.data.task_result}</td>
        </tr>`
      $('#tasks').prepend(html);
      const taskStatus = res.data.task_status;
      if (taskStatus === 'finished' || taskStatus === 'failed') return false;
      setTimeout(function() {
        getStatus(res.data.task_id);
      }, 1000);
    })
    .fail((err) => {
      console.log(err)
    });
  }
  
});





