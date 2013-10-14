{% if user.is_authenticated() %}  
 self.badgePoints = ko.observable("{{ user.get_badge().get('score') }}");

 self.gradeQuiz = function() {
   $.ajax({
      type: 'POST',
       url: '/calcon-2013-session/grade',
       data: $('#badge-quiz').serialize(),
       success: function(response) {
         if(response['error']) {
           alert("Error " + response['error'])
         } else {
          alert("Graded Quiz " + response['score'] + " out of 4");
          var existing_points = parseInt(self.badgePoints());
          var new_total = existing_points + parseInt(response['score']);
          self.badgePoints(new_total);
         }
       }
    });
 }
{% endif %}
