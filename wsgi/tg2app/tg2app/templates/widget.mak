<%inherit file="local:templates.master"/>

	<script type="text/javascript">
	$(document).ready(function() {
    	setTimeout(function(){		
        	$('#from_date').datepicker('setDate', $.query.get('from_date'));
        	$('#to_date').datepicker('setDate', $.query.get('to_date'));
		    $('.ui-datepicker').hide();
    	}, 250);
	});
	</script>

<table><tr><td>${title} from</td>
<td>${c.from_date_widget.display() | n}</td>
<td>to</td><td>${c.to_date_widget.display() | n}</td></tr></table>
<div id="content">
${widget.display() | n}
</div>
